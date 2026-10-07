import json
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.agents.career import ROLE_SKILLS
from app.agents.registry import AGENTS, is_valid_action
from app.agents.runner import run_agent
from app.core.config import settings
from app.core.permissions import PermissionEngine
from app.core.ratelimit import rate_limit
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import (ActivityLog, AgentPermission, Document, Notification, PendingApproval,
                           TrackedProduct, User)

log = logging.getLogger("jeevanai.agents")
router = APIRouter(prefix="/api", tags=["agents"])
policy = PermissionEngine()


class AgentRequest(BaseModel):
    agent: str
    action: str
    message: str = Field(default="", max_length=20000)
    payload: dict = Field(default_factory=dict)


class AgentRunOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    status: str
    agent: Optional[str] = None
    action: Optional[str] = None
    message: Optional[str] = None
    approval_id: Optional[int] = None
    response: Optional[str] = None
    mode: Optional[str] = None
    data: Optional[dict] = None


def _log(db: Session, user_id: int, agent: str, action: str, status: str, details: str = ""):
    db.add(ActivityLog(user_id=user_id, agent=agent, action=action, status=status, details=(details or "")[:2000]))
    db.commit()


def _execute(db: Session, user_id: int, agent: str, action: str, message: str, payload: dict):
    try:
        result = run_agent(agent, action, message, payload, db, user_id)
    except ValueError as e:
        db.rollback()
        _log(db, user_id, agent, action, "failed", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        db.rollback()
        log.exception("Agent crashed")
        _log(db, user_id, agent, action, "error", "internal error")
        raise HTTPException(status_code=500, detail="Agent failed unexpectedly")
    _log(db, user_id, agent, action, "completed", message)
    return result


@router.get("/agents")
def list_agents(user: User = Depends(get_current_user)):
    return AGENTS


@router.get("/meta")
def meta(user: User = Depends(get_current_user)):
    return {"roles": list(ROLE_SKILLS)}


@router.post("/agent/run", response_model=AgentRunOut,
             dependencies=[Depends(rate_limit(settings.rate_limit_per_minute))])
def execute_agent(request: AgentRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if request.agent not in AGENTS:
        raise HTTPException(status_code=404, detail="Agent not found")
    if not is_valid_action(request.agent, request.action):
        raise HTTPException(status_code=400, detail=f"Unknown action for {request.agent}: {request.action}")

    row = db.scalar(select(AgentPermission).where(
        AgentPermission.user_id == user.id, AgentPermission.agent == request.agent,
        AgentPermission.action == request.action))
    decision = policy.decide(row.permission if row else "ASK")

    if decision["status"] == "blocked":
        _log(db, user.id, request.agent, request.action, "blocked", request.message)
        return {"status": "blocked", "message": decision["message"], "agent": request.agent, "action": request.action}

    if decision["status"] == "approval_required":
        pending = PendingApproval(user_id=user.id, agent=request.agent, action=request.action,
                                  message=request.message, payload=json.dumps(request.payload))
        db.add(pending)
        db.commit()
        db.refresh(pending)
        _log(db, user.id, request.agent, request.action, "approval_required", request.message)
        return {"status": "approval_required", "message": decision["message"], "approval_id": pending.id,
                "agent": request.agent, "action": request.action}

    result = _execute(db, user.id, request.agent, request.action, request.message, request.payload)
    return {"status": "allowed", **result}


def _own_approval(db: Session, user: User, approval_id: int) -> PendingApproval:
    a = db.scalar(select(PendingApproval).where(PendingApproval.id == approval_id, PendingApproval.user_id == user.id))
    if not a:
        raise HTTPException(status_code=404, detail="Approval not found")
    if a.status != "pending":
        raise HTTPException(status_code=409, detail=f"Already {a.status}")
    a.decided_at = datetime.now(timezone.utc)
    return a


@router.get("/approvals")
def list_approvals(status: Optional[str] = "pending", db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    q = select(PendingApproval).where(PendingApproval.user_id == user.id)
    if status:
        q = q.where(PendingApproval.status == status)
    rows = db.scalars(q.order_by(PendingApproval.id.desc()).limit(100)).all()
    return [{"id": a.id, "agent": a.agent, "action": a.action, "message": a.message,
             "payload": json.loads(a.payload or "{}"), "status": a.status, "created_at": a.created_at}
            for a in rows]


@router.post("/approvals/{approval_id}/approve", response_model=AgentRunOut)
def approve(approval_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = _own_approval(db, user, approval_id)
    row = db.scalar(select(AgentPermission).where(
        AgentPermission.user_id == user.id, AgentPermission.agent == a.agent, AgentPermission.action == a.action))
    if row and row.permission.upper() == "BLOCK":
        a.status = "rejected"
        db.commit()
        raise HTTPException(status_code=403, detail="This action is now blocked by policy")
    a.status = "approved"
    db.commit()
    result = _execute(db, user.id, a.agent, a.action, a.message, json.loads(a.payload or "{}"))
    return {"status": "approved", "approval_id": a.id, **result}


@router.post("/approvals/{approval_id}/reject")
def reject(approval_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = _own_approval(db, user, approval_id)
    a.status = "rejected"
    db.commit()
    _log(db, user.id, a.agent, a.action, "rejected", a.message)
    return {"status": "rejected", "approval_id": a.id}


@router.get("/activity")
def activity(limit: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    limit = max(1, min(limit, 200))
    rows = db.scalars(select(ActivityLog).where(ActivityLog.user_id == user.id)
                      .order_by(ActivityLog.id.desc()).limit(limit)).all()
    return [{"id": r.id, "agent": r.agent, "action": r.action, "status": r.status,
             "details": r.details, "created_at": r.created_at} for r in rows]


def _count(db: Session, model, *conds) -> int:
    return db.scalar(select(func.count()).select_from(model).where(*conds)) or 0


@router.get("/stats")
def stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    uid = user.id
    recent = db.scalars(select(ActivityLog).where(ActivityLog.user_id == uid)
                        .order_by(ActivityLog.id.desc()).limit(5)).all()
    return {
        "completed": _count(db, ActivityLog, ActivityLog.user_id == uid, ActivityLog.status == "completed"),
        "blocked": _count(db, ActivityLog, ActivityLog.user_id == uid, ActivityLog.status == "blocked"),
        "pending_approvals": _count(db, PendingApproval, PendingApproval.user_id == uid, PendingApproval.status == "pending"),
        "documents": _count(db, Document, Document.user_id == uid),
        "products": _count(db, TrackedProduct, TrackedProduct.user_id == uid),
        "unread_alerts": _count(db, Notification, Notification.user_id == uid, Notification.is_read.is_(False)),
        "recent": [{"agent": r.agent, "action": r.action, "status": r.status, "created_at": r.created_at}
                   for r in recent],
    }
