from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.agents.registry import is_valid_action
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import AgentPermission, User
from app.db.seed import seed_user_permissions

router = APIRouter(prefix="/api/permissions", tags=["permissions"])


class PermissionUpdate(BaseModel):
    agent: str
    action: str
    permission: str


@router.get("")
def list_permissions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(AgentPermission).where(AgentPermission.user_id == user.id)
                      .order_by(AgentPermission.agent, AgentPermission.action)).all()
    return [{"id": r.id, "agent": r.agent, "action": r.action, "permission": r.permission} for r in rows]


@router.post("")
def update_permission(payload: PermissionUpdate, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    value = payload.permission.upper()
    if value not in {"ALLOW", "ASK", "BLOCK"}:
        raise HTTPException(status_code=400, detail="Use ALLOW, ASK or BLOCK")
    if not is_valid_action(payload.agent, payload.action):
        raise HTTPException(status_code=400, detail="Unknown agent/action")
    row = db.scalar(select(AgentPermission).where(
        AgentPermission.user_id == user.id, AgentPermission.agent == payload.agent,
        AgentPermission.action == payload.action))
    if row:
        row.permission = value
    else:
        row = AgentPermission(user_id=user.id, agent=payload.agent, action=payload.action, permission=value)
        db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "agent": row.agent, "action": row.action, "permission": row.permission}


@router.post("/reset")
def reset_permissions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    seed_user_permissions(db, user.id, reset=True)
    return {"reset": True}
