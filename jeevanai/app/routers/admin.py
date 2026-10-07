from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import require_admin
from app.db.database import get_db
from app.db.models import ActivityLog, Document, PendingApproval, TrackedProduct, User
from app.routers.auth import user_dict
from app.schemas import ActiveIn, AdminUserOut, RoleIn, iso

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
def stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    by_state = (db.query(User.state, func.count(User.id)).group_by(User.state)
                .order_by(func.count(User.id).desc()).limit(10).all())
    return {
        "users": db.query(User).count(),
        "active_users": db.query(User).filter(User.is_active.is_(True)).count(),
        "admins": db.query(User).filter(User.role == "admin").count(),
        "agent_runs": db.query(ActivityLog).count(),
        "documents": db.query(Document).count(),
        "products": db.query(TrackedProduct).count(),
        "pending_approvals": db.query(PendingApproval).filter(PendingApproval.status == "pending").count(),
        "by_state": [{"state": s or "Not set", "count": c} for s, c in by_state],
    }


@router.get("/users", response_model=List[AdminUserOut])
def list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(User).order_by(User.id.desc()).all()
    return [{**user_dict(u), "is_active": u.is_active is not False, "last_login": iso(u.last_login)} for u in rows]


def _target(db: Session, admin: User, user_id: int) -> User:
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if u.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot change your own account here")
    return u


@router.post("/users/{user_id}/active")
def set_active(user_id: int, body: ActiveIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    u = _target(db, admin, user_id)
    u.is_active = body.active
    db.commit()
    return {"id": u.id, "is_active": u.is_active}


@router.post("/users/{user_id}/role")
def set_role(user_id: int, body: RoleIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    u = _target(db, admin, user_id)
    if body.role == "user" and u.email in settings.admin_emails:
        raise HTTPException(status_code=400, detail="This user is an admin in the .env file (ADMIN_EMAIL)")
    u.role = body.role
    db.commit()
    return {"id": u.id, "role": u.role}
