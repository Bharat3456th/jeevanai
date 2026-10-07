from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.ratelimit import RateLimiter, client_ip
from app.core.regions import OCCUPATIONS, STATES
from app.core.security import (DUMMY_HASH, create_token, get_current_user, hash_password, sync_admin,
                               verify_password)
from app.db.database import get_db
from app.db.models import User
from app.db.seed import seed_user_permissions
from app.schemas import (LoginIn, PasswordChange, ProfileUpdate, RegisterIn, TokenOut, UserOut, iso)

router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = RateLimiter(20, 60)


def user_dict(u: User) -> dict:
    return {"id": u.id, "email": u.email, "name": u.name or "", "role": u.role or "user", "phone": u.phone,
            "state": u.state, "city": u.city, "occupation": u.occupation, "dob": u.dob,
            "created_at": iso(u.created_at),
            "profile_complete": bool(u.phone and u.state and u.city and u.occupation and u.dob)}


def _out(user: User) -> dict:
    return {"access_token": create_token(user.id), "token_type": "bearer", "user": user_dict(user)}


@router.get("/meta")
def meta():
    """Lists used by the registration/profile forms (no login needed)."""
    return {"states": [{"name": n, "lang": l} for n, l in STATES], "occupations": OCCUPATIONS}


@router.post("/register", response_model=TokenOut)
def register(body: RegisterIn, request: Request, db: Session = Depends(get_db)):
    limiter.check(client_ip(request))
    if not settings.allow_registration:
        raise HTTPException(status_code=403, detail="Registration is disabled")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="This email is already registered")
    first_user = db.query(User).count() == 0
    user = User(email=body.email, name=body.name, phone=body.phone, state=body.state, city=body.city,
                occupation=body.occupation, dob=body.dob, password_hash=hash_password(body.password),
                role="admin" if first_user else "user", is_active=True,
                last_login=datetime.now(timezone.utc))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This email is already registered")
    db.refresh(user)
    seed_user_permissions(db, user.id)
    sync_admin(db, user)
    return _out(user)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    limiter.check(client_ip(request))
    user = db.query(User).filter(User.email == body.email.strip().lower()).first()
    ok = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not ok:
        raise HTTPException(status_code=401, detail="Wrong email or password")
    if user.is_active is False:
        raise HTTPException(status_code=403, detail="This account is disabled. Please contact the admin.")
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    sync_admin(db, user)
    return _out(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user_dict(user)


@router.put("/me", response_model=UserOut)
def update_me(body: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.name, user.phone, user.state = body.name, body.phone, body.state
    user.city, user.occupation, user.dob = body.city, body.occupation, body.dob
    db.commit()
    db.refresh(user)
    return user_dict(user)


@router.post("/change-password")
def change_password(body: PasswordChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(body.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Old password is wrong")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"ok": True}
