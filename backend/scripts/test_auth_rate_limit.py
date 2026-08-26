"""
scripts/test_auth_rate_limit.py
-------------------------------
Verifies the new authentication hardening logic:
- Account-specific locks after MAX_LOGIN_ATTEMPTS.
- Success resets counters.
- Lock expiration allows subsequent logins.
- IP rate limits (slowapi) allow 20+ successful logins without 429s.
"""

import sys
import random
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

sys.path.insert(0, ".")
from app.main import app
from app.api.deps import get_db
from app.models.user import User

client = TestClient(app)
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

def get_db_session() -> Session:
    return next(get_db())

print("--- Authentication Hardening Tests ---")

# Setup users
reg1 = f"U1_{rand}"
pass1 = "SecurePass123"
check(
    "Setup User 1 (201)",
    client.post("/auth/register/student", json={
        "full_name": "Test User 1",
        "email": f"u1_{rand}@test.edu",
        "password": pass1,
        "registration_number": reg1,
    }),
    201
)

reg2 = f"U2_{rand}"
pass2 = "SecurePass123"
check(
    "Setup User 2 (201)",
    client.post("/auth/register/student", json={
        "full_name": "Test User 2",
        "email": f"u2_{rand}@test.edu",
        "password": pass2,
        "registration_number": reg2,
    }),
    201
)

# TEST 1: Correct login repeated 20 times -> all succeed (tests IP rate limit is relaxed)
print("\n[TEST 1] Correct login 20 times (IP Limit Check)")
success = True
for i in range(20):
    r = client.post("/auth/login", json={"registration_number": reg1, "password": pass1})
    if r.status_code != 200:
        success = False
        errors.append(f"T1 Failed on attempt {i+1}: {r.status_code}")
        break
print(f"{'PASS' if success else 'FAIL'}  TEST 1: 20 successful logins")

# TEST 2 & 3: Wrong password 5 times -> locked on 5th failure, 6th attempt blocked
print("\n[TEST 2 & 3] Account Lock after 5 failures")
for i in range(5):
    check(f"Failed attempt {i+1} (401)", 
          client.post("/auth/login", json={"registration_number": reg1, "password": "wrong"}), 
          401)

r_lock = check("Attempt 6 should be blocked (429)", 
               client.post("/auth/login", json={"registration_number": reg1, "password": pass1}), 
               429)

if r_lock.status_code == 429:
    print(f"  Lock message: {r_lock.json().get('detail')}")

# TEST 4: Different registration number -> still allowed
print("\n[TEST 4] Different account independence")
check("User 2 logs in successfully while User 1 is locked (200)",
      client.post("/auth/login", json={"registration_number": reg2, "password": pass2}),
      200)

# TEST 5: Successful login after failures resets counter
print("\n[TEST 5] Reset counter on success")
# Cause 3 failures on User 2
for i in range(3):
    client.post("/auth/login", json={"registration_number": reg2, "password": "wrong"})
# Success on 4th
check("User 2 logs in successfully (200)",
      client.post("/auth/login", json={"registration_number": reg2, "password": pass2}),
      200)
# Next failure should be attempt 1, not 4 (so not locked)
client.post("/auth/login", json={"registration_number": reg2, "password": "wrong"})
check("User 2 still not locked (401, not 429)",
      client.post("/auth/login", json={"registration_number": reg2, "password": "wrong"}),
      401)

# TEST 6 & 7: JWT and /auth/me
print("\n[TEST 6 & 7] JWT and /auth/me")
token = client.post("/auth/login", json={"registration_number": reg2, "password": pass2}).json()["access_token"]
check("Get /auth/me with new JWT (200)",
      client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}),
      200)

# LOCK EXPIRATION VERIFICATION
print("\n[LOCK EXPIRATION VERIFICATION]")
# User 1 is currently locked. Let's modify the DB to simulate time passing.
db = get_db_session()
u1 = db.query(User).filter(User.registration_number == reg1).first()
if u1 and u1.locked_until:
    # Rewind locked_until to 1 minute ago
    u1.locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    print("  Simulated lock expiration in DB...")
else:
    errors.append("Lock expiration setup failed: User 1 not locked in DB.")

# Now login should succeed
check("User 1 login succeeds after lock expires (200)",
      client.post("/auth/login", json={"registration_number": reg1, "password": pass1}),
      200)

db.refresh(u1)
if u1.failed_login_attempts != 0 or u1.locked_until is not None:
    errors.append(f"Lock reset failed in DB. attempts={u1.failed_login_attempts}, locked={u1.locked_until}")
else:
    print("  DB verified: counters and lock cleared.")

# Check OAuth2 endpoint shared logic
print("\n[TEST OAUTH2 ENDPOINT]")
# Lock User 2 via OAuth2
for i in range(5):
    client.post("/auth/token", data={"username": reg2, "password": "wrong"})
check("OAuth2 attempt 6 is locked (429)",
      client.post("/auth/token", data={"username": reg2, "password": pass2}),
      429)

print()
if errors:
    print(f"FAILURES ({len(errors)}):")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("ALL RATE LIMITING TESTS PASSED.")
