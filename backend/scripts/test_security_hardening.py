"""
scripts/test_security_hardening.py
------------------------------------
Phase 3.2.1 Security Hardening — full verification test suite.

Updated in Pre-Phase 3.6:
    - All upload calls now supply resume_type form field.
    - Extraction HTTP endpoints removed from regression (now internal pipeline).
    - Limit test updated: MAX_RESUMES_PER_STUDENT = 2 (1 generic + 1 specialized).
    - Replacement behavior tested: uploading same type replaces old resume.

Runs:
    - Original Phase 3.2 regression tests (updated for resume_type)
    - Phase 3.2.1 Security Hardening tests:
        S1:  Fake PDF (EXE magic bytes renamed .pdf)
        S2:  Fake PDF (plain text renamed .pdf)
        S3:  Fake DOCX (plain text renamed .docx)
        S4:  Corrupted PDF (valid header, broken body)
        S5:  Corrupted DOCX (PK header, random garbage)
        S6:  Path traversal filename (stored safely via UUID)
        S7:  Resume count limit (MAX_RESUMES_PER_STUDENT = 2)
        S8:  Invalid resume_type rejected
"""

import io
import random
import sys
import uuid
import zipfile

from fastapi.testclient import TestClient

sys.path.insert(0, ".")
from app.main import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=True)
errors = []
rand = random.randint(10000, 99999)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def check(label: str, resp, expected_status: int, check_fn=None):
    ok = resp.status_code == expected_status
    if check_fn and ok:
        try:
            ok = ok and check_fn(resp.json())
        except Exception as e:
            ok = False
            errors.append(f"{label}: body check error: {e}")
    status_str = "PASS" if ok else "FAIL"
    if not ok:
        errors.append(
            f"{label}: expected {expected_status}, got {resp.status_code}. "
            f"body={resp.text[:300]}"
        )
    print(f"{status_str}  {label}")
    return resp


def make_real_pdf() -> bytes:
    """Build a valid, parseable minimal PDF."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f\n"
        b"0000000009 00000 n\n"
        b"0000000058 00000 n\n"
        b"0000000115 00000 n\n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\n"
        b"startxref\n190\n%%EOF"
    )


def make_unique_pdf(marker: str = "") -> bytes:
    """Build a unique valid parseable PDF with embedded unique content (different hash each call)."""
    unique_tag = f"{marker}_{rand}_{uuid.uuid4().hex[:8]}"
    content = f"Student Resume {unique_tag}\nSkills: Python, FastAPI\nEducation: B.Tech CS"
    escaped = content.replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 50 700 Td ({escaped}) Tj ET"
    stream_bytes = stream.encode("latin-1")
    stream_len = len(stream_bytes)
    pdf = (
        f"%PDF-1.4\n"
        f"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        f"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        f"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        f"4 0 obj\n<< /Length {stream_len} >>\nstream\n{stream}\nendstream\nendobj\n"
        f"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        f"xref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n"
        f"0000000115 00000 n\n0000000250 00000 n\n0000000350 00000 n\n"
        f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n450\n%%EOF"
    )
    return pdf.encode("latin-1")


def make_real_docx() -> bytes:
    """Build a valid, parseable minimal DOCX (python-docx compatible)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>",
        )
        zf.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>Test Resume</w:t></w:r></w:p></w:body>"
            "</w:document>",
        )
        zf.writestr(
            "word/_rels/document.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            "</Relationships>",
        )
    return buf.getvalue()


REAL_PDF = make_real_pdf()
REAL_DOCX = make_real_docx()


# ---------------------------------------------------------------------------
# Setup: Student + Faculty accounts
# ---------------------------------------------------------------------------

stu_reg = f"SEC{rand}"
r = client.post(
    "/auth/register/student",
    json={
        "full_name": "SecStudent",
        "email": f"sec_{rand}@test.edu",
        "password": "SecurePass1234",
        "registration_number": stu_reg,
    },
)
assert r.status_code == 201, f"Student registration failed: {r.text}"

r = client.post(
    "/auth/login",
    json={"registration_number": stu_reg, "password": "SecurePass1234"},
)
stu_token = r.json()["access_token"]
hdrs = {"Authorization": f"Bearer {stu_token}"}

r2 = client.post(
    "/auth/register/faculty",
    json={
        "full_name": "Faculty",
        "email": f"fac_sec_{rand}@test.edu",
        "password": "SecurePass1234",
        "registration_number": f"FAC{rand}",
    },
)
fac_token = client.post(
    "/auth/login",
    json={"registration_number": f"FAC{rand}", "password": "SecurePass1234"},
).json()["access_token"]
fac_hdrs = {"Authorization": f"Bearer {fac_token}"}


# ---------------------------------------------------------------------------
# Phase 3.2 Regression Tests (updated for resume_type)
# ---------------------------------------------------------------------------

print("--- Phase 3.2 Regression Tests (resume_type aware) ---")

# Upload generic PDF
r = check(
    "Upload valid PDF as generic (201)",
    client.post(
        "/resume/upload",
        files={"file": ("my_resume.pdf", io.BytesIO(REAL_PDF), "application/pdf")},
        data={"resume_type": "generic"},
        headers=hdrs,
    ),
    201,
    lambda b: (
        b.get("file_name") == "my_resume.pdf"
        and b.get("file_type") == ".pdf"
        and b.get("resume_type") == "generic"
        and b.get("processing_status") == "uploaded"
        and "id" in b
    ),
)
first_resume_id = r.json().get("id") if r.status_code == 201 else None

# Upload specialized DOCX
r2 = check(
    "Upload valid DOCX as specialized (201)",
    client.post(
        "/resume/upload",
        files={"file": ("resume.docx", io.BytesIO(REAL_DOCX), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"resume_type": "specialized"},
        headers=hdrs,
    ),
    201,
    lambda b: b.get("file_type") == ".docx" and b.get("resume_type") == "specialized",
)
specialized_resume_id = r2.json().get("id") if r2.status_code == 201 else None

# Verify we now have 2 resumes
check(
    "List resumes — total=2 (200)",
    client.get("/resume", headers=hdrs),
    200,
    lambda b: b.get("total") == 2 and len(b.get("resumes", [])) == 2,
)

# Upload duplicate content (same bytes = same hash = 409)
check(
    "Upload duplicate PDF content (409)",
    client.post(
        "/resume/upload",
        files={"file": ("my_resume.pdf", io.BytesIO(REAL_PDF), "application/pdf")},
        data={"resume_type": "generic"},
        headers=hdrs,
    ),
    409,
)

check(
    "Upload .exe (400)",
    client.post(
        "/resume/upload",
        files={"file": ("virus.exe", io.BytesIO(b"MZ" + b"x" * 100), "application/octet-stream")},
        data={"resume_type": "generic"},
        headers=hdrs,
    ),
    400,
)

check(
    "Upload empty file (400)",
    client.post(
        "/resume/upload",
        files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        data={"resume_type": "generic"},
        headers=hdrs,
    ),
    400,
)

big_bytes = b"%PDF-1.4 " + b"x" * (10 * 1024 * 1024 + 1)
check(
    "Upload >10MB file (400)",
    client.post(
        "/resume/upload",
        files={"file": ("big.pdf", io.BytesIO(big_bytes), "application/pdf")},
        data={"resume_type": "generic"},
        headers=hdrs,
    ),
    400,
)

check(
    "Faculty upload blocked (403)",
    client.post(
        "/resume/upload",
        files={"file": ("r.pdf", io.BytesIO(REAL_PDF), "application/pdf")},
        data={"resume_type": "generic"},
        headers=fac_hdrs,
    ),
    403,
)

check(
    "Unauthenticated upload (401)",
    client.post(
        "/resume/upload",
        files={"file": ("r.pdf", io.BytesIO(REAL_PDF), "application/pdf")},
        data={"resume_type": "generic"},
    ),
    401,
)

check("Faculty list blocked (403)", client.get("/resume", headers=fac_hdrs), 403)

if first_resume_id:
    check(
        "Get own resume (200)",
        client.get(f"/resume/{first_resume_id}", headers=hdrs),
        200,
        lambda b: b.get("id") == first_resume_id,
    )
    check(
        "Faculty get resume blocked (403)",
        client.get(f"/resume/{first_resume_id}", headers=fac_hdrs),
        403,
    )

check(
    "Get nonexistent resume (404)",
    client.get(f"/resume/{uuid.uuid4()}", headers=hdrs),
    404,
)

if first_resume_id:
    check(
        "Delete own generic resume (204)",
        client.delete(f"/resume/{first_resume_id}", headers=hdrs),
        204,
    )
    check(
        "Get deleted resume (404)",
        client.get(f"/resume/{first_resume_id}", headers=hdrs),
        404,
    )

check(
    "Delete nonexistent resume (404)",
    client.delete(f"/resume/{uuid.uuid4()}", headers=hdrs),
    404,
)


# ---------------------------------------------------------------------------
# Phase 3.2.1 Security Hardening Tests
# ---------------------------------------------------------------------------

print()
print("--- Phase 3.2.1 Security Hardening Tests ---")

# S1: EXE renamed to .pdf
fake_pdf_exe = b"MZ\x90\x00" + b"x" * 200
check(
    "S1: Fake PDF (EXE magic bytes) rejected (400)",
    client.post(
        "/resume/upload",
        files={"file": ("malware.pdf", io.BytesIO(fake_pdf_exe), "application/pdf")},
        data={"resume_type": "generic"},
        headers=hdrs,
    ),
    400,
)

# S2: Plain text renamed .pdf
text_as_pdf = b"Hello, I am definitely not a PDF file at all."
check(
    "S2: Fake PDF (plain text renamed .pdf) rejected (400)",
    client.post(
        "/resume/upload",
        files={"file": ("notapdf.pdf", io.BytesIO(text_as_pdf), "application/pdf")},
        data={"resume_type": "generic"},
        headers=hdrs,
    ),
    400,
)

# S3: Plain text renamed .docx
text_as_docx = b"I am just a text file pretending to be a DOCX document."
check(
    "S3: Fake DOCX (plain text renamed .docx) rejected (400)",
    client.post(
        "/resume/upload",
        files={"file": ("notadocx.docx", io.BytesIO(text_as_docx), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"resume_type": "specialized"},
        headers=hdrs,
    ),
    400,
)

# S4: Corrupted PDF
corrupted_pdf = b"%PDF-1.4 corrupted garbage that pdfplumber cannot parse " + b"\x00\xff\xfe" * 20
check(
    "S4: Corrupted PDF (valid header, broken body) rejected (400)",
    client.post(
        "/resume/upload",
        files={"file": ("corrupt.pdf", io.BytesIO(corrupted_pdf), "application/pdf")},
        data={"resume_type": "generic"},
        headers=hdrs,
    ),
    400,
)

# S5: Corrupted DOCX
corrupted_docx = b"PK\x03\x04" + b"\xff\xfe\xab\xcd" * 60
check(
    "S5: Corrupted DOCX (PK magic, broken archive) rejected (400)",
    client.post(
        "/resume/upload",
        files={"file": ("corrupt.docx", io.BytesIO(corrupted_docx), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"resume_type": "specialized"},
        headers=hdrs,
    ),
    400,
)

# S6: Path traversal filename — must succeed (stored safely as UUID on disk)
# After the earlier delete, student has 1 specialized resume. Generic slot is free.
check(
    "S6: Path traversal filename stored safely (201)",
    client.post(
        "/resume/upload",
        files={"file": ("../../../etc/passwd.pdf", io.BytesIO(REAL_PDF), "application/pdf")},
        data={"resume_type": "generic"},
        headers=hdrs,
    ),
    201,
)

# S7: Resume type limit — student now has: generic + specialized = 2 resumes
# Test: upload another variant of generic — it should REPLACE the existing generic (201).
# We use make_unique_pdf() to generate a completely different PDF (unique hash) so the
# duplicate-content check passes and only the type-replacement logic is exercised.
check(
    "S7: Replace existing generic resume (201) — replacement acts as safety valve",
    client.post(
        "/resume/upload",
        files={"file": (f"updated_generic_{rand}.pdf", io.BytesIO(make_unique_pdf("s7")), "application/pdf")},
        data={"resume_type": "generic"},
        headers=hdrs,
    ),
    201,
)

# Verify still only 2 resumes after replacement
check(
    "S7b: Total resumes still 2 after replacement (200)",
    client.get("/resume", headers=hdrs),
    200,
    lambda b: b.get("total") == 2,
)

# S8: Invalid resume_type value rejected
check(
    "S8: Invalid resume_type value rejected (422)",
    client.post(
        "/resume/upload",
        files={"file": ("r.pdf", io.BytesIO(REAL_PDF), "application/pdf")},
        data={"resume_type": "executive"},
        headers=hdrs,
    ),
    422,
)


# ---------------------------------------------------------------------------
# Final result
# ---------------------------------------------------------------------------

print()
if errors:
    print(f"FAILURES ({len(errors)}):")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    total = 16 + 9  # 16 regression + 9 security tests
    print(f"All {total} tests passed (16 regression + 9 security hardening).")
