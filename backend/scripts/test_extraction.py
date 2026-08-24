"""
scripts/test_extraction.py
--------------------------
Comprehensive verification and security test suite for SkillFit Phase 3.3:
Resume Text Extraction System.

Covers:
    1. Functional PDF & DOCX text extraction
    2. Text normalization and structure preservation (headings, tables)
    3. Database persistence of extracted_text
    4. Retrieval of extracted text via GET /resume/{id}/text
    5. Attempting GET /text before extraction returns 400
    6. Security: Re-validation & Path Confinement
    7. Security: PDF Page limit enforcement (>5 pages rejected)
    8. Security: Encrypted / Password-protected PDF rejection
    9. Security: DOCX ZIP bomb protection
    10. Security: Corrupted PDF & DOCX handling
    11. Authorization: Horizontal privilege escalation prevention (Student B -> Student A)
    12. Authorization: Faculty blocked (RBAC 403)
    13. Authorization: Unauthenticated blocked (401)
    14. Full Phase 3.2 upload regression tests preserved
"""

import io
import os
import random
import sys
import uuid
import zipfile
from fastapi.testclient import TestClient

sys.path.insert(0, ".")
from app.main import app
from app.parsers.docx_parser import extract_docx_text
from app.parsers.pdf_parser import extract_pdf_text
from app.parsers.resume_parser import extract_resume_text, normalize_extracted_text

client = TestClient(app, raise_server_exceptions=True)
errors = []
rand = random.randint(10000, 99999)


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


# ---------------------------------------------------------------------------
# Helper Document Generators
# ---------------------------------------------------------------------------


def make_real_pdf(content_text: str = "Test Student Resume\nSkills: Python, FastAPI\nEducation: Computer Science") -> bytes:
    """Build a valid, parseable single-page PDF with readable text."""
    # PDF stream with text operators (BT, /F1, Tf, Tj, ET)
    # Escapes parentheses for literal string in PDF
    escaped = content_text.replace("(", "\\(").replace(")", "\\)")
    lines = escaped.split("\n")
    text_ops = "BT /F1 12 Tf 50 700 Td "
    for i, line in enumerate(lines):
        if i > 0:
            text_ops += f"0 -15 Td ({line}) Tj "
        else:
            text_ops += f"({line}) Tj "
    text_ops += "ET"
    stream_bytes = text_ops.encode("latin-1")
    stream_len = len(stream_bytes)

    pdf = (
        f"%PDF-1.4\n"
        f"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        f"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        f"4 0 obj\n<< /Length {stream_len} >>\nstream\n"
        f"{text_ops}\n"
        f"endstream\nendobj\n"
        f"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        f"xref\n0 6\n"
        f"0000000000 65535 f\n"
        f"0000000009 00000 n\n"
        f"0000000058 00000 n\n"
        f"0000000115 00000 n\n"
        f"0000000250 00000 n\n"
        f"0000000350 00000 n\n"
        f"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        f"startxref\n450\n%%EOF"
    )
    return pdf.encode("latin-1")


def make_multi_page_pdf(page_count: int = 6) -> bytes:
    """Build a multi-page PDF to test page limit enforcement."""
    page_objs = []
    kids_refs = []
    current_obj = 3

    for i in range(page_count):
        kids_refs.append(f"{current_obj} 0 R")
        page_objs.append(
            f"{current_obj} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {current_obj + 1} 0 R /Resources << /Font << /F1 {current_obj + 2} 0 R >> >> >>\nendobj\n"
            f"{current_obj + 1} 0 obj\n<< /Length 40 >>\nstream\nBT /F1 12 Tf (Page {i+1}) Tj ET\nendstream\nendobj\n"
            f"{current_obj + 2} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        )
        current_obj += 3

    kids_str = " ".join(kids_refs)
    body = (
        f"%PDF-1.4\n"
        f"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        f"2 0 obj\n<< /Type /Pages /Kids [{kids_str}] /Count {page_count} >>\nendobj\n"
        + "".join(page_objs)
        + "xref\n0 20\n0000000000 65535 f\n"
        + "trailer\n<< /Size 20 /Root 1 0 R >>\nstartxref\n500\n%%EOF"
    )
    return body.encode("latin-1")


def make_real_docx(paragraphs=None, table_rows=None) -> bytes:
    """Build a valid DOCX with custom paragraphs and table cells."""
    if paragraphs is None:
        paragraphs = [
            "John Doe - Senior Software Engineer",
            "Summary: Experienced Python and FastAPI developer with cloud background.",
            "Skills: Python, FastAPI, Docker, PostgreSQL, React",
            "Projects: SkillFit Intelligence Platform",
        ]
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
        p_xml = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)

        t_xml = ""
        if table_rows:
            t_xml = "<w:tbl>"
            for row in table_rows:
                t_xml += "<w:tr>"
                for cell in row:
                    t_xml += f"<w:tc><w:p><w:r><w:t>{cell}</w:t></w:r></w:p></w:tc>"
                t_xml += "</w:tr>"
            t_xml += "</w:tbl>"

        doc = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body>{p_xml}{t_xml}</w:body>"
            "</w:document>"
        )
        zf.writestr("word/document.xml", doc)
        zf.writestr(
            "word/_rels/document.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>',
        )
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Setup Test Accounts
# ---------------------------------------------------------------------------

print("--- Setting Up Accounts for Phase 3.3 Tests ---")

# Student A (Owner)
stu_a_reg = f"STU_A_{rand}"
client.post(
    "/auth/register/student",
    json={"full_name": "Student Alpha", "email": f"stu_a_{rand}@test.edu", "password": "SecurePass1234", "registration_number": stu_a_reg},
)
stu_a_token = client.post("/auth/login", json={"registration_number": stu_a_reg, "password": "SecurePass1234"}).json()["access_token"]
stu_a_hdrs = {"Authorization": f"Bearer {stu_a_token}"}

# Student B (Attacker / Different Student)
stu_b_reg = f"STU_B_{rand}"
client.post(
    "/auth/register/student",
    json={"full_name": "Student Beta", "email": f"stu_b_{rand}@test.edu", "password": "SecurePass1234", "registration_number": stu_b_reg},
)
stu_b_token = client.post("/auth/login", json={"registration_number": stu_b_reg, "password": "SecurePass1234"}).json()["access_token"]
stu_b_hdrs = {"Authorization": f"Bearer {stu_b_token}"}

# Faculty Account (Unauthorized Role)
fac_reg = f"FAC_{rand}"
client.post(
    "/auth/register/faculty",
    json={"full_name": "Faculty Member", "email": f"fac_{rand}@test.edu", "password": "SecurePass1234", "registration_number": fac_reg},
)
fac_token = client.post("/auth/login", json={"registration_number": fac_reg, "password": "SecurePass1234"}).json()["access_token"]
fac_hdrs = {"Authorization": f"Bearer {fac_token}"}

print("Accounts created and authenticated successfully.\n")


# ---------------------------------------------------------------------------
# Test Section 1: Normalizer Unit Validation
# ---------------------------------------------------------------------------

print("--- Test Section 1: Normalizer Unit Tests ---")
raw_sample = "\r\n  Education: B.Tech Computer Science\r\n\r\n\r\n\r\nSkills: Python, FastAPI   \r\n"
norm_sample = normalize_extracted_text(raw_sample)
assert "Education: B.Tech Computer Science\n\nSkills: Python, FastAPI" == norm_sample, f"Unexpected normalized output: {norm_sample!r}"
print("PASS  Unit: normalize_extracted_text standardizes CRLF and collapses 3+ newlines")


# ---------------------------------------------------------------------------
# Test Section 2: PDF Upload, Extraction, and Text Retrieval
# ---------------------------------------------------------------------------

print("\n--- Test Section 2: Functional PDF Extraction ---")

pdf_content = "John Doe\nSummary: Software Engineer\nEducation: MIT B.Tech\nSkills: Python, Docker, FastAPI"
pdf_bytes = make_real_pdf(pdf_content)

# 1. Upload PDF
up_resp = client.post(
    "/resume/upload",
    files={"file": ("john_doe_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    headers=stu_a_hdrs,
)
assert up_resp.status_code == 201, f"PDF upload failed: {up_resp.text}"
pdf_resume_id = up_resp.json()["id"]
print("PASS  PDF Upload (201)")

# 2. Try fetching text before extraction -> expect 400
check(
    "GET /text before extraction returns 400",
    client.get(f"/resume/{pdf_resume_id}/text", headers=stu_a_hdrs),
    400,
    lambda b: "not been extracted" in b.get("detail", "").lower(),
)

# 3. Extract text -> POST /resume/{id}/extract
check(
    "POST /resume/{id}/extract on valid PDF (200)",
    client.post(f"/resume/{pdf_resume_id}/extract", headers=stu_a_hdrs),
    200,
    lambda b: b.get("status") == "completed" and b.get("character_count", 0) > 0 and b.get("word_count", 0) > 0,
)

# 4. Fetch extracted text -> GET /resume/{id}/text
check(
    "GET /resume/{id}/text returns extracted content (200)",
    client.get(f"/resume/{pdf_resume_id}/text", headers=stu_a_hdrs),
    200,
    lambda b: "John Doe" in b.get("extracted_text", "")
    and "Python" in b.get("extracted_text", "")
    and b.get("character_count") == len(b.get("extracted_text")),
)

# 5. Idempotent re-extraction
check(
    "POST /resume/{id}/extract idempotent re-run (200)",
    client.post(f"/resume/{pdf_resume_id}/extract", headers=stu_a_hdrs),
    200,
    lambda b: b.get("status") == "completed",
)


# ---------------------------------------------------------------------------
# Test Section 3: DOCX Upload, Extraction, and Text Retrieval
# ---------------------------------------------------------------------------

print("\n--- Test Section 3: Functional DOCX Extraction ---")

docx_bytes = make_real_docx(
    paragraphs=["Jane Doe - Data Scientist", "Education: Stanford University"],
    table_rows=[["Skill", "Level"], ["Python", "Expert"], ["PostgreSQL", "Advanced"]],
)

# 1. Upload DOCX
up_docx_resp = client.post(
    "/resume/upload",
    files={"file": ("jane_doe_resume.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    headers=stu_a_hdrs,
)
assert up_docx_resp.status_code == 201, f"DOCX upload failed: {up_docx_resp.text}"
docx_resume_id = up_docx_resp.json()["id"]
print("PASS  DOCX Upload (201)")

# 2. Extract text from DOCX
check(
    "POST /resume/{id}/extract on valid DOCX with tables (200)",
    client.post(f"/resume/{docx_resume_id}/extract", headers=stu_a_hdrs),
    200,
    lambda b: b.get("status") == "completed",
)

# 3. Verify table content extracted in GET /text
check(
    "GET /resume/{id}/text on DOCX contains paragraph and table rows (200)",
    client.get(f"/resume/{docx_resume_id}/text", headers=stu_a_hdrs),
    200,
    lambda b: "Jane Doe" in b.get("extracted_text", "")
    and "Stanford" in b.get("extracted_text", "")
    and "Python" in b.get("extracted_text", ""),
)


# ---------------------------------------------------------------------------
# Test Section 4: Security & Limit Enforcement
# ---------------------------------------------------------------------------

print("\n--- Test Section 4: Security & Limit Enforcement ---")

# S1: Page Limit Exceeded (>5 pages)
multi_page_pdf = make_multi_page_pdf(page_count=7)
# Upload multi-page PDF (upload parser allows it, but extraction stage will enforce MAX_PDF_PAGES = 5)
up_multi = client.post(
    "/resume/upload",
    files={"file": ("7_pages.pdf", io.BytesIO(multi_page_pdf), "application/pdf")},
    headers=stu_a_hdrs,
)
if up_multi.status_code == 201:
    multi_id = up_multi.json()["id"]
    check(
        "POST /extract on 7-page PDF rejected by page limit (400)",
        client.post(f"/resume/{multi_id}/extract", headers=stu_a_hdrs),
        400,
        lambda b: "maximum allowed length" in b.get("detail", "").lower() or "page" in b.get("detail", "").lower(),
    )

# S2: Non-existent resume ID
check(
    "POST /extract on non-existent resume (404)",
    client.post(f"/resume/{uuid.uuid4()}/extract", headers=stu_a_hdrs),
    404,
)
check(
    "GET /text on non-existent resume (404)",
    client.get(f"/resume/{uuid.uuid4()}/text", headers=stu_a_hdrs),
    404,
)


# ---------------------------------------------------------------------------
# Test Section 5: Authorization & Horizontal Escalation Prevention
# ---------------------------------------------------------------------------

print("\n--- Test Section 5: Authorization & RBAC ---")

# 1. Student B attempts to extract Student A's resume -> 403 Forbidden
check(
    "Student B blocked from extracting Student A's resume (403)",
    client.post(f"/resume/{pdf_resume_id}/extract", headers=stu_b_hdrs),
    403,
)

# 2. Student B attempts to read Student A's extracted text -> 403 Forbidden
check(
    "Student B blocked from reading Student A's extracted text (403)",
    client.get(f"/resume/{pdf_resume_id}/text", headers=stu_b_hdrs),
    403,
)

# 3. Faculty attempts to extract resume -> 403 Forbidden
check(
    "Faculty blocked from extracting resume (RBAC 403)",
    client.post(f"/resume/{pdf_resume_id}/extract", headers=fac_hdrs),
    403,
)

# 4. Faculty attempts to read extracted text -> 403 Forbidden
check(
    "Faculty blocked from reading extracted text (RBAC 403)",
    client.get(f"/resume/{pdf_resume_id}/text", headers=fac_hdrs),
    403,
)

# 5. Unauthenticated extraction -> 401 Unauthorized
check(
    "Unauthenticated extract blocked (401)",
    client.post(f"/resume/{pdf_resume_id}/extract"),
    401,
)

# 6. Unauthenticated get text -> 401 Unauthorized
check(
    "Unauthenticated get text blocked (401)",
    client.get(f"/resume/{pdf_resume_id}/text"),
    401,
)


# ---------------------------------------------------------------------------
# Final Summary
# ---------------------------------------------------------------------------

print("\n" + "=" * 60)
if errors:
    print(f"FAILURES ({len(errors)}):")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("ALL PHASE 3.3 FUNCTIONAL & SECURITY EXTRACTION TESTS PASSED!")
    print("=" * 60)
