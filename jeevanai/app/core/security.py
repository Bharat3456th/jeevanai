import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.database import get_db
from app.db.models import User

_bearer = HTTPBearer(auto_error=False)
ITERATIONS = 390_000
DUMMY_HASH = "pbkdf2$390000$" + base64.b64encode(b"0" * 16).decode() + "$" + base64.b64encode(b"0" * 32).decode()


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, it, salt, digest = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt), int(it))
        return hmac.compare_digest(dk, base64.b64decode(digest))
    except Exception:  # noqa: BLE001
        return False


def create_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(minutes=settings.jwt_expire_minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(_bearer),
                     db: Session = Depends(get_db)) -> User:
    if not creds:
        raise HTTPException(status_code=401, detail="Please log in")
    try:
        data = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=["HS256"])
        user = db.get(User, int(data["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Session expired. Please log in again")
    if not user:
        raise HTTPException(status_code=401, detail="Account not found")
    if user.is_active is False:
        raise HTTPException(status_code=403, detail="This account is disabled. Please contact the admin.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def sync_admin(db: Session, user: User) -> None:
    """Emails listed in ADMIN_EMAIL always have the admin role."""
    if user.email in settings.admin_emails and user.role != "admin":
        user.role = "admin"
        db.commit()
