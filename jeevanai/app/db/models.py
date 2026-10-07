from datetime import datetime, timezone
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text)
from datetime import datetime, timezone
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text,
                        UniqueConstraint)
from sqlalchemy.orm import synonym
from .database import Base


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), default="")
    password_hash = Column(String(300), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # "user" or "admin"
    phone = Column(String(20), nullable=True)
    state = Column(String(60), nullable=True)
    city = Column(String(80), nullable=True)
    occupation = Column(String(60), nullable=True)
    dob = Column(String(10), nullable=True)  # YYYY-MM-DD
    is_active = Column(Boolean, nullable=False, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=now)


class AgentPermission(Base):
    __tablename__ = "agent_permissions"
    __table_args__ = (UniqueConstraint("user_id", "agent", "action", name="uq_user_agent_action"),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    agent = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    permission = Column(String(20), nullable=False, default="ASK")
    created_at = Column(DateTime, default=now)


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    agent = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False)
    details = Column(Text, default="")
    created_at = Column(DateTime, default=now)


class PendingApproval(Base):
    """An ASK-level action waiting for the user to approve or reject."""
    __tablename__ = "pending_approvals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    agent = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    message = Column(Text, default="")
    payload = Column(Text, default="{}")
    status = Column(String(20), nullable=False, default="pending")  # pending/approved/rejected
    created_at = Column(DateTime, default=now)
    decided_at = Column(DateTime, nullable=True)


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=now)


class TrackedProduct(Base):
    __tablename__ = "tracked_products"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(200), default="")
    url = Column(Text, nullable=False)
    target_price = Column(Float, nullable=True)
    alert_enabled = Column(Boolean, default=False)
    alert_sent = Column(Boolean, default=False)
    last_price = Column(Float, nullable=True)
    currency = Column(String(10), default="")
    last_checked = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=now)


class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("tracked_products.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="")
    checked_at = Column(DateTime, default=now)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    body = Column(Text, default="")
    read = Column(Boolean, default=False)
    is_read = synonym("read")
    created_at = Column(DateTime, default=now)
