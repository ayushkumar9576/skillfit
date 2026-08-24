"""
scripts/test_swagger_oauth2.py
------------------------------
Verifies OAuth2 form-data authentication (/auth/token) and Swagger UI integration.
"""

import io
import random
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, ".")
from app.main import app

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


print("--- Testing OAuth2 Form Login & Swagger UI Authorize Flow ---")

# 1. Register a student
reg_num = f"SWAGGER_{rand}"
email = f"swagger_{rand}@test.edu"
password = "SecurePassword123"

r = client.post(
    "/auth/register/student",
    json={
        "full_name": "Swagger Tester",
        "email": email,
        "password": password,
        "registration_number": reg_num,
    },
)
assert r.status_code == 201, f"Registration failed: {r.text}"
print("PASS  Student registration (201)")

# 2. Test JSON login (POST /auth/login) backward compatibility
check(
    "JSON login with registration_number (200)",
    client.post("/auth/login", json={"registration_number": reg_num, "password": password}),
    200,
    lambda b: "access_token" in b and b.get("token_type") == "bearer",
)

# 3. Test OAuth2 form login (POST /auth/token) with registration_number
r_token = check(
    "OAuth2 form login with username=registration_number (200)",
    client.post("/auth/token", data={"username": reg_num, "password": password}),
    200,
    lambda b: "access_token" in b and b.get("token_type") == "bearer",
)
token = r_token.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 4. Test OAuth2 form login (POST /auth/token) with username=email
check(
    "OAuth2 form login with username=email (200)",
    client.post("/auth/token", data={"username": email, "password": password}),
    200,
    lambda b: "access_token" in b and b.get("token_type") == "bearer",
)

# 5. Test OAuth2 form login with bad password (401)
check(
    "OAuth2 form login with invalid password (401)",
    client.post("/auth/token", data={"username": reg_num, "password": "WrongPassword"}),
    401,
)

# 6. Test OAuth2 form login with non-existent user (401)
check(
    "OAuth2 form login with unknown user (401)",
    client.post("/auth/token", data={"username": "NONEXISTENT", "password": password}),
    401,
)

# 7. Check OpenAPI specification component
openapi = client.get("/openapi.json").json()
oauth2_scheme = openapi.get("components", {}).get("securitySchemes", {}).get("OAuth2PasswordBearer", {})
flows = oauth2_scheme.get("flows", {}).get("password", {})
token_url = flows.get("tokenUrl")
assert token_url == "/auth/token", f"Unexpected tokenUrl in OpenAPI: {token_url}"
print(f"PASS  OpenAPI security scheme correctly configured with tokenUrl='{token_url}'")

# 8. Use the OAuth2-acquired token on GET /auth/me
check(
    "GET /auth/me using OAuth2 Bearer token (200)",
    client.get("/auth/me", headers=headers),
    200,
    lambda b: b.get("registration_number") == reg_num and b.get("email") == email,
)

# 9. Use the OAuth2-acquired token on POST /resume/upload
pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n4 0 obj\n<< /Length 45 >>\nstream\nBT /F1 12 Tf 50 700 Td (Swagger Test Resume) Tj ET\nendstream\nendobj\n5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000250 00000 n\n0000000345 00000 n\ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n445\n%%EOF"

up_r = check(
    "POST /resume/upload using OAuth2 Bearer token (201)",
    client.post(
        "/resume/upload",
        files={"file": ("swagger_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers=headers,
    ),
    201,
)
resume_id = up_r.json()["id"]

# 10. Use the OAuth2-acquired token on POST /resume/{id}/extract
check(
    "POST /resume/{id}/extract using OAuth2 Bearer token (200)",
    client.post(f"/resume/{resume_id}/extract", headers=headers),
    200,
    lambda b: b.get("status") == "completed",
)

# 11. Use the OAuth2-acquired token on GET /resume/{id}/text
check(
    "GET /resume/{id}/text using OAuth2 Bearer token (200)",
    client.get(f"/resume/{resume_id}/text", headers=headers),
    200,
    lambda b: "Swagger Test Resume" in b.get("extracted_text", ""),
)

print("\n" + "=" * 60)
if errors:
    print(f"FAILURES ({len(errors)}):")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("ALL SWAGGER OAUTH2 & JWT TESTS PASSED!")
    print("=" * 60)
