import io
import re
from typing import List, Dict, Any, Tuple
import magic
import openpyxl
from pydantic import EmailStr, validate_email
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
from app.core.security import hash_password
from app.models.user import User
from app.models.student import Student
from app.models.faculty import Faculty
from app.models.import_audit_log import ImportAuditLog, ImportType, ImportStatus
from app.core.enums import UserRole

MAX_ROWS_LIMIT = 1000
ALLOWED_MIME_TYPES = [
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/zip",
    "application/octet-stream"
]

def validate_excel_file(file: UploadFile) -> bytes:
    content = file.file.read()
    file.file.seek(0)

    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 5MB limit."
        )

    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES or not file.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only .xlsx files are allowed."
        )
    return content


def process_bulk_import(
    db: Session,
    file: UploadFile,
    import_type: ImportType,
    admin_id: str
) -> Dict[str, Any]:
    content = validate_excel_file(file)
    
    try:
        # Load the workbook securely
        wb = openpyxl.load_workbook(filename=io.BytesIO(content), data_only=True, read_only=True)
        ws = wb.active
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to parse Excel file."
        )

    rows = list(ws.iter_rows(values_only=True))
    if not rows or len(rows) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty or missing headers."
        )

    headers = [str(h).strip().lower() for h in rows[0] if h is not None]
    required_headers = ["full name", "email", "registration number"]
    
    for rh in required_headers:
        if rh not in headers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required column: {rh}"
            )
            
    name_idx = headers.index("full name")
    email_idx = headers.index("email")
    reg_idx = headers.index("registration number")

    data_rows = rows[1:]
    if len(data_rows) > MAX_ROWS_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exceeded maximum row limit of {MAX_ROWS_LIMIT}."
        )

    errors = []
    processed_records = []
    
    seen_emails = set()
    seen_regs = set()

    for idx, row in enumerate(data_rows, start=2):
        if not any(row):  # Skip completely empty rows
            continue
            
        full_name = str(row[name_idx]).strip() if len(row) > name_idx and row[name_idx] else ""
        email = str(row[email_idx]).strip().lower() if len(row) > email_idx and row[email_idx] else ""
        reg_no = str(row[reg_idx]).strip().upper() if len(row) > reg_idx and row[reg_idx] else ""

        row_errors = []
        if not full_name:
            row_errors.append("Missing full name.")
        if not email:
            row_errors.append("Missing email.")
        else:
            try:
                # Basic email validation
                validate_email(email)
            except Exception:
                row_errors.append("Invalid email format.")

        if not reg_no:
            row_errors.append("Missing registration number.")
        elif not re.match(r"^[A-Z0-9]+$", reg_no):
            row_errors.append("Invalid registration number format.")

        if email in seen_emails:
            row_errors.append("Duplicate email in file.")
        if reg_no in seen_regs:
            row_errors.append("Duplicate registration number in file.")
            
        seen_emails.add(email)
        seen_regs.add(reg_no)

        if row_errors:
            errors.append({"row": idx, "message": " | ".join(row_errors)})
        else:
            processed_records.append({
                "full_name": full_name,
                "email": email,
                "registration_number": reg_no
            })

    # Validate against database if no file-level errors
    if not errors:
        db_emails = {u[0] for u in db.query(User.email).filter(User.email.in_(list(seen_emails))).all()}
        db_regs = {u[0] for u in db.query(User.registration_number).filter(User.registration_number.in_(list(seen_regs))).all()}
        
        for idx, row in enumerate(data_rows, start=2):
            if not any(row): continue
            
            email = str(row[email_idx]).strip().lower() if len(row) > email_idx and row[email_idx] else ""
            reg_no = str(row[reg_idx]).strip().upper() if len(row) > reg_idx and row[reg_idx] else ""
            
            if email in db_emails:
                errors.append({"row": idx, "message": "Email already exists in database."})
            if reg_no in db_regs:
                errors.append({"row": idx, "message": "Registration number already exists in database."})

    total_rows = len(processed_records)
    
    if errors:
        # Create FAILED audit log for validation failure
        audit_log = ImportAuditLog(
            admin_id=admin_id,
            import_type=import_type,
            file_name=file.filename,
            total_rows=len(data_rows),
            imported_rows=0,
            failed_rows=len(data_rows),
            status=ImportStatus.FAILED,
            error_summary="Validation failed for one or more rows. Check errors list."
        )
        db.add(audit_log)
        db.commit()
        
        # Atomic failure response
        return {
            "success": False,
            "errors": errors
        }
        
    try:
        # Perform transactional inserts
        for rec in processed_records:
            user = User(
                full_name=rec["full_name"],
                email=rec["email"],
                registration_number=rec["registration_number"],
                password_hash=hash_password(rec["registration_number"]),
                role=UserRole.student if import_type == ImportType.STUDENT else UserRole.faculty,
                is_active=True,
                email_verified=False,
                requires_password_change=True,
                last_login_at=None
            )
            db.add(user)
            db.flush()
            
            if import_type == ImportType.STUDENT:
                student = Student(
                    user_id=user.id,
                    registration_number=rec["registration_number"],
                    branch=None
                )
                db.add(student)
            elif import_type == ImportType.FACULTY:
                faculty = Faculty(
                    user_id=user.id,
                    registration_number=rec["registration_number"],
                    department=None
                )
                db.add(faculty)

        audit_log = ImportAuditLog(
            admin_id=admin_id,
            import_type=import_type,
            file_name=file.filename,
            total_rows=total_rows,
            imported_rows=total_rows,
            failed_rows=0,
            status=ImportStatus.SUCCESS
        )
        db.add(audit_log)
        db.commit()

        return {
            "success": True,
            "processed": total_rows,
            "created": total_rows,
            "failed": 0
        }
    except Exception as e:
        db.rollback()
        
        # Create FAILED audit log for unexpected exception
        try:
            audit_log = ImportAuditLog(
                admin_id=admin_id,
                import_type=import_type,
                file_name=file.filename,
                total_rows=len(data_rows) if 'data_rows' in locals() else 0,
                imported_rows=0,
                failed_rows=len(data_rows) if 'data_rows' in locals() else 0,
                status=ImportStatus.FAILED,
                error_summary=f"Unexpected exception: {str(e)}"
            )
            db.add(audit_log)
            db.commit()
        except Exception:
            db.rollback() # Failsafe if audit log insertion fails
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transaction failed. Rolled back."
        )
