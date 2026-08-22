import sys
import random
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import require_roles, get_current_user
from app.core.enums import UserRole
from app.db.database import SessionLocal
from app.models.user import User

# Add temporary routes to app for RBAC testing
rbac_router = APIRouter(prefix="/rbac-test")

@rbac_router.get("/student")
def student_only(current_user: User = Depends(require_roles(UserRole.student))):
    return {"message": "Success", "role": current_user.role}

@rbac_router.get("/faculty")
def faculty_only(current_user: User = Depends(require_roles(UserRole.faculty))):
    return {"message": "Success", "role": current_user.role}

app.include_router(rbac_router)

client = TestClient(app)

errors = []
rand = random.randint(10000, 99999)

def log_result(name, ok, details=""):
    status = "PASS" if ok else "FAIL"
    print(f"{status} | {name} {details}")
    if not ok:
        errors.append(name)

print("--- RBAC Verification ---")

# Register test users
student_reg = f"RBAC_STU_{rand}"
faculty_reg = f"RBAC_FAC_{rand}"

res_stu = client.post("/auth/register/student", json={
    "full_name": "Test Student", "email": f"stu{rand}@college.edu",
    "password": "SecurePass1234", "registration_number": student_reg
})
log_result("Register Student", res_stu.status_code == 201)

res_fac = client.post("/auth/register/faculty", json={
    "full_name": "Test Faculty", "email": f"fac{rand}@college.edu",
    "password": "SecurePass1234", "registration_number": faculty_reg
})
log_result("Register Faculty", res_fac.status_code == 201)

# Login
token_stu = client.post("/auth/login", json={"registration_number": student_reg, "password": "SecurePass1234"}).json()["access_token"]
token_fac = client.post("/auth/login", json={"registration_number": faculty_reg, "password": "SecurePass1234"}).json()["access_token"]

# RBAC Tests
headers_stu = {"Authorization": f"Bearer {token_stu}"}
headers_fac = {"Authorization": f"Bearer {token_fac}"}

res1 = client.get("/rbac-test/student", headers=headers_stu)
log_result("Student accessing StudentOnly route", res1.status_code == 200, f"(Expected 200, Got {res1.status_code})")

res2 = client.get("/rbac-test/faculty", headers=headers_stu)
log_result("Student accessing FacultyOnly route", res2.status_code == 403, f"(Expected 403, Got {res2.status_code})")

res3 = client.get("/rbac-test/faculty", headers=headers_fac)
log_result("Faculty accessing FacultyOnly route", res3.status_code == 200, f"(Expected 200, Got {res3.status_code})")

res4 = client.get("/rbac-test/student", headers=headers_fac)
log_result("Faculty accessing StudentOnly route", res4.status_code == 403, f"(Expected 403, Got {res4.status_code})")

print("\n--- Rate Limiting Verification ---")

# Login Endpoint Limit (5 per 15 minutes)
# We already logged in twice above, but TestClient might reset state or they might count against the limit.
# Let's generate a random reg number so it fails authentication but still hits the rate limiter.
# Wait, SlowAPI limits based on IP, so the TestClient IP (usually 'testclient') is used.
limit_login = 5

# We already hit /auth/login twice above. We hit it 3 more times to reach the limit of 5.
for i in range(3):
    res = client.post("/auth/login", json={"registration_number": "fake", "password": "fake"})
    log_result(f"Login request {i+3}/5", res.status_code == 401, f"(Expected 401, Got {res.status_code})")

# 6th request should be 429
res_limit = client.post("/auth/login", json={"registration_number": "fake", "password": "fake"})
log_result("Login request 6/5 (Rate Limited)", res_limit.status_code == 429, f"(Expected 429, Got {res_limit.status_code})")

# Registration Limits (10 per hour)
# We registered 1 student above. Let's do 9 more.
for i in range(9):
    r = f"RL_STU_{rand}_{i}"
    res = client.post("/auth/register/student", json={
        "full_name": "Test", "email": f"{r}@c.edu", "password": "SecurePass1234", "registration_number": r
    })
    log_result(f"Register request {i+2}/10", res.status_code == 201, f"(Expected 201, Got {res.status_code})")

res_limit_reg = client.post("/auth/register/student", json={
    "full_name": "Test", "email": f"RL_STU_{rand}_ex@c.edu", "password": "SecurePass1234", "registration_number": f"RL_STU_{rand}_ex"
})
log_result("Register request 11/10 (Rate Limited)", res_limit_reg.status_code == 429, f"(Expected 429, Got {res_limit_reg.status_code})")

print()
if errors:
    print(f"FAILED TESTS: {len(errors)}")
    sys.exit(1)
else:
    print("ALL VERIFICATIONS PASSED")
