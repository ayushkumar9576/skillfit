"""
scripts/test_security_hardening.py
------------------------------------
Phase 3.2.1 Security Hardening — full verification test suite.

Runs:
    - Original 16 Phase 3.2 regression tests (ensure no breakage)
    - New security hardening tests:
        S1:  Fake PDF (EXE magic bytes renamed .pdf)
        S2:  Fake PDF (plain text renamed .pdf)
        S3:  Fake DOCX (plain text renamed .docx)
        S4:  Corrupted PDF (valid header, broken body)
        S5:  Corrupted DOCX (PK header, random garbage)
        S6:  Path traversal filename (stored safely via UUID)
        S7:  Resume count limit (MAX_RESUMES_PER_STUDENT)
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
    status = "PASS" if ok else "FAIL"
    if not ok:
        errors.append(
            f"{label}: expected {expected_status}, got {resp.status_code}. "
            f"body={resp.text[:300]}"
        )
    print(f"{status}  {label}")
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
# Original Phase 3.2 Regression Tests (16 tests)
# ---------------------------------------------------------------------------

print("--- Original Phase 3.2 Regression Tests ---")

r = check(
    "Upload valid PDF (201)",
    client.post(
        "/resume/upload",
        files={"file": ("my_resume.pdf", io.BytesIO(REAL_PDF), "application/pdf")},
        headers=hdrs,
    ),
    201,
    lambda b: b.get("file_name") == "my_resume.pdf"
    and b.get("file_type") == ".pdf"
    and "id" in b,
)
first_resume_id = r.json().get("id") if r.status_code == 201 else None

check(
    "Upload valid DOCX (201)",
    client.post(
        "/resume/upload",
        files={"file": ("resume.docx", io.BytesIO(REAL_DOCX), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=hdrs,
    ),
    201,
    lambda b: b.get("file_type") == ".docx",
)

check(
    "Upload duplicate PDF (409)",
    client.post(
        "/resume/upload",
        files={"file": ("my_resume.pdf", io.BytesIO(REAL_PDF), "application/pdf")},
        headers=hdrs,
    ),
    409,
)

check(
    "Upload .exe (400)",
    client.post(
        "/resume/upload",
        files={"file": ("virus.exe", io.BytesIO(b"MZ" + b"x" * 100), "application/octet-stream")},
        headers=hdrs,
    ),
    400,
)

check(
    "Upload empty file (400)",
    client.post(
        "/resume/upload",
        files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
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
        headers=hdrs,
    ),
    400,
)

check(
    "Faculty upload blocked (403)",
    client.post(
        "/resume/upload",
        files={"file": ("r.pdf", io.BytesIO(REAL_PDF), "application/pdf")},
        headers=fac_hdrs,
    ),
    403,
)

check(
    "Unauthenticated upload (401)",
    client.post(
        "/resume/upload",
        files={"file": ("r.pdf", io.BytesIO(REAL_PDF), "application/pdf")},
    ),
    401,
)

check(
    "List resumes (200)",
    client.get("/resume", headers=hdrs),
    200,
    lambda b: b.get("total") == 2 and len(b.get("resumes", [])) == 2,
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
        "Delete own resume (204)",
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

# S1: EXE renamed to .pdf (Windows PE magic bytes — should fail signature + MIME + parser)
fake_pdf_exe = b"MZ\x90\x00" + b"x" * 200
check(
    "S1: Fake PDF (EXE magic bytes) rejected (400)",
    client.post(
        "/resume/upload",
        files={"file": ("malware.pdf", io.BytesIO(fake_pdf_exe), "application/pdf")},
        headers=hdrs,
    ),
    400,
)

# S2: Plain text renamed .pdf (should fail signature + parser)
text_as_pdf = b"Hello, I am definitely not a PDF file at all."
check(
    "S2: Fake PDF (plain text renamed .pdf) rejected (400)",
    client.post(
        "/resume/upload",
        files={"file": ("notapdf.pdf", io.BytesIO(text_as_pdf), "application/pdf")},
        headers=hdrs,
    ),
    400,
)

# S3: Plain text renamed .docx (should fail signature + parser)
text_as_docx = b"I am just a text file pretending to be a DOCX document."
check(
    "S3: Fake DOCX (plain text renamed .docx) rejected (400)",
    client.post(
        "/resume/upload",
        files={"file": ("notadocx.docx", io.BytesIO(text_as_docx), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=hdrs,
    ),
    400,
)

# S4: Corrupted PDF (valid header but body is garbage — parser should fail)
corrupted_pdf = b"%PDF-1.4 corrupted garbage that pdfplumber cannot parse " + b"\x00\xff\xfe" * 20
check(
    "S4: Corrupted PDF (valid header, broken body) rejected (400)",
    client.post(
        "/resume/upload",
        files={"file": ("corrupt.pdf", io.BytesIO(corrupted_pdf), "application/pdf")},
        headers=hdrs,
    ),
    400,
)

# S5: Corrupted DOCX (PK header but random garbage — parser should fail)
corrupted_docx = b"PK\x03\x04" + b"\xff\xfe\xab\xcd" * 60
check(
    "S5: Corrupted DOCX (PK magic, broken archive) rejected (400)",
    client.post(
        "/resume/upload",
        files={"file": ("corrupt.docx", io.BytesIO(corrupted_docx), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=hdrs,
    ),
    400,
)

# S6: Path traversal filename — must be stored safely via UUID (not on disk at traversal path)
# A real valid PDF with a malicious filename. Should succeed — the filename is only
# stored as metadata; the disk file is always a UUID.
check(
    "S6: Path traversal filename handled safely (201)",
    client.post(
        "/resume/upload",
        files={"file": ("../../../etc/passwd.pdf", io.BytesIO(REAL_PDF), "application/pdf")},
        headers=hdrs,
    ),
    201,
)

# S7: Resume count limit
# Current state: 1 DOCX + 1 path-traversal PDF = 2 resumes
# Upload 3 more to reach MAX_RESUMES_PER_STUDENT (5)
for i in range(3):
    pdf_variant = bytearray(REAL_PDF)
    variant_bytes = f"variant_{rand}_{i}".encode()
    pdf_variant[5:5 + len(variant_bytes)] = variant_bytes
    check(
        f"S7a: Upload within limit resume {i + 3}/5 (201)",
        client.post(
            "/resume/upload",
            files={"file": (f"r{i}.pdf", io.BytesIO(bytes(pdf_variant)), "application/pdf")},
            headers=hdrs,
        ),
        201,
    )

# Now at 5 — next upload should be blocked with 400
pdf_over_limit = bytearray(REAL_PDF)
pdf_over_limit[5:15] = b"overlimit!"
check(
    "S7b: Upload when at limit (400)",
    client.post(
        "/resume/upload",
        files={"file": ("overlimit.pdf", io.BytesIO(bytes(pdf_over_limit)), "application/pdf")},
        headers=hdrs,
    ),
    400,
    lambda b: "limit" in b.get("detail", "").lower(),
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
    total = 16 + 8  # 16 regression + 8 security tests
    print(f"All {total} tests passed (16 regression + 8 security hardening).")
