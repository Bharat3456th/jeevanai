from sqlalchemy import select
from sqlalchemy.orm import Session
from app.agents.registry import DEFAULT_PERMISSIONS
from app.db.models import AgentPermission


def seed_user_permissions(db: Session, user_id: int, reset: bool = False):
    rows = {(r.agent, r.action): r for r in
            db.scalars(select(AgentPermission).where(AgentPermission.user_id == user_id))}
    for (agent, action), perm in DEFAULT_PERMISSIONS.items():
        row = rows.get((agent, action))
        if row is None:
            db.add(AgentPermission(user_id=user_id, agent=agent, action=action, permission=perm))
        elif reset:
            row.permission = perm
    db.commit()
