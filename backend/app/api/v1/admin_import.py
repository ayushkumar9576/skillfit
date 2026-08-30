import io
from fastapi import APIRouter, Depends, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import openpyxl

from app.api.deps import get_db, require_roles
from app.core.enums import UserRole
from app.models.user import User
from app.models.import_audit_log import ImportType
from app.services.bulk_import_service import process_bulk_import

router = APIRouter(prefix="/api/v1/admin/import", tags=["Admin — Bulk Import"])

@router.post("/students", summary="Bulk import students via Excel")
def import_students(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.admin)),
):
    """
    Accepts an Excel file containing: Full Name, Email, Registration Number.
    Creates Student accounts, enforces requires_password_change, and creates an audit log.
    Atomic transaction: fails completely if any row is invalid.
    """
    return process_bulk_import(db, file, ImportType.STUDENT, admin.id)


@router.post("/faculty", summary="Bulk import faculty via Excel")
def import_faculty(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.admin)),
):
    """
    Accepts an Excel file containing: Full Name, Email, Registration Number.
    Creates Faculty accounts, enforces requires_password_change, and creates an audit log.
    Atomic transaction: fails completely if any row is invalid.
    """
    return process_bulk_import(db, file, ImportType.FACULTY, admin.id)


def _generate_template(filename: str, sample_row: list[str]):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Import Template"
    
    headers = ["Full Name", "Email", "Registration Number"]
    ws.append(headers)
    ws.append(sample_row)
    
    # Make headers bold
    for cell in ws[1]:
        cell.font = openpyxl.styles.Font(bold=True)

    # Adjust column widths
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 20
        
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/templates/student", summary="Download student import template")
def download_student_template(
    _: User = Depends(require_roles(UserRole.admin)),
):
    return _generate_template("student_import_template.xlsx", ["John Doe", "john@college.edu", "22BCE001"])

@router.get("/templates/faculty", summary="Download faculty import template")
def download_faculty_template(
    _: User = Depends(require_roles(UserRole.admin)),
):
    return _generate_template("faculty_import_template.xlsx", ["Dr. Sharma", "sharma@college.edu", "FAC001"])
