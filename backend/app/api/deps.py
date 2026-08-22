"""
app/api/deps.py
---------------
Reusable FastAPI dependency functions for SkillFit.

Phase 2 dependencies:
    - get_db()           — yields a SQLAlchemy database session
    - get_current_user() — decodes JWT and returns the authenticated User ORM object

Usage in route handlers:
    @router.get("/auth/me")
    def me(current_user: User = Depends(get_current_user)):
        ...

Design:
    - Dependencies raise HTTPException directly so FastAPI handles the
      error response automatically.
    - get_current_user is intentionally strict: any malformed, expired, or
      tampered token results in a 401 — there is no "optional auth" variant
      in Phase 2.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session
from typing import Callable, Any

from app.core.enums import UserRole
from app.core.security import decode_access_token
from app.db.database import SessionLocal
from app.models.user import User

# FastAPI's OAuth2PasswordBearer reads the Authorization: Bearer <token> header.
# tokenUrl is the login endpoint — used by the OpenAPI /docs UI only.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")



def get_db():
    """
    Yield a SQLAlchemy database session for the duration of a single request.

    Guarantees the session is closed (and any pending transaction rolled back)
    even if an exception is raised during request handling.

    Usage:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the JWT Bearer token and return the corresponding User ORM object.

    Validates:
        - Token signature and expiry (via decode_access_token)
        - "sub" claim is present and is a valid UUID
        - User exists in the database
        - User account is active (is_active=True)

    Args:
        token: JWT string extracted from the Authorization header by OAuth2PasswordBearer.
        db:    Database session from get_db().

    Returns:
        The authenticated User ORM object, with .student or .faculty
        relationship accessible (lazy-loaded on first access).

    Raises:
        HTTPException 401 — for any of: invalid token, expired token,
                            missing "sub" claim, user not found, inactive account.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user: User | None = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account has been deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# ---------------------------------------------------------------------------
# Authorization dependencies (RBAC)
# ---------------------------------------------------------------------------


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    """
    Dependency factory for Role-Based Access Control.

    Returns a dependency that checks if the authenticated user has one of
    the allowed roles.

    Raises:
        HTTPException 403 — if the user's role is not in allowed_roles.

    Usage:
        Depends(require_roles(UserRole.student))
        Depends(require_roles(UserRole.faculty, UserRole.admin))
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
        return current_user

    return role_checker
