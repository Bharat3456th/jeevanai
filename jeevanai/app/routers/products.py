from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import Notification, TrackedProduct, User

router = APIRouter(prefix="/api", tags=["products"])


@router.get("/products")
def list_products(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(TrackedProduct).where(TrackedProduct.user_id == user.id)
                      .order_by(TrackedProduct.id.desc())).all()
    return [{"id": p.id, "name": p.name, "url": p.url, "target_price": p.target_price,
             "alert_enabled": bool(p.alert_enabled), "last_price": p.last_price, "currency": p.currency,
             "last_checked": p.last_checked} for p in rows]


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = db.scalar(select(TrackedProduct).where(TrackedProduct.id == product_id, TrackedProduct.user_id == user.id))
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(p)
    db.commit()
    return {"deleted": product_id}


@router.get("/notifications")
def list_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id)
                      .order_by(Notification.id.desc()).limit(100)).all()
    return [{"id": n.id, "title": n.title, "body": n.body, "is_read": bool(n.is_read),
             "created_at": n.created_at} for n in rows]


@router.post("/notifications/read")
def mark_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    for n in db.scalars(select(Notification).where(Notification.user_id == user.id,
                                                   Notification.is_read.is_(False))).all():
        n.is_read = True
    db.commit()
    return {"ok": True}
