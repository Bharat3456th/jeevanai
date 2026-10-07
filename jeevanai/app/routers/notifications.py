from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import Notification, User
from app.schemas import iso

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Bell + Alerts page ke liye: {"unread": N, "items": [...]}"""
    rows = (db.query(Notification).filter(Notification.user_id == user.id)
            .order_by(Notification.id.desc()).limit(50).all())
    unread = db.query(Notification).filter(Notification.user_id == user.id,
                                           Notification.read.is_(False)).count()
    return {"unread": unread,
            "items": [{"id": n.id, "title": n.title, "body": n.body or "",
                       "read": bool(n.read), "created_at": iso(n.created_at)} for n in rows]}


@router.post("/read-all")
def read_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.user_id == user.id,
                                  Notification.read.is_(False)).update({Notification.read: True})
    db.commit()
    return {"ok": True}