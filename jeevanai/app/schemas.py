import re
from datetime import date, timezone
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator
from app.core.regions import OCCUPATIONS, STATE_NAMES

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def iso(dt) -> Optional[str]:
    """UTC ISO string with Z so browsers show the right local time."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.isoformat() + "Z"


class _ProfileFields(BaseModel):
    name: str = Field(max_length=100)
    phone: str = Field(max_length=20)
    state: str = Field(max_length=60)
    city: str = Field(max_length=80)
    occupation: str = Field(max_length=60)
    dob: str = Field(max_length=10)

    @field_validator("name", "city")
    @classmethod
    def _text(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name and city must have at least 2 letters")
        return v

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        digits = re.sub(r"[\s\-()]", "", v)
        digits = re.sub(r"^(\+91|91|0)", "", digits) if len(digits) > 10 else digits
        if not re.fullmatch(r"[6-9]\d{9}", digits):
            raise ValueError("Enter a valid 10 digit Indian mobile number")
        return digits

    @field_validator("state")
    @classmethod
    def _state(cls, v: str) -> str:
        if v not in STATE_NAMES:
            raise ValueError("Select your state / UT from the list")
        return v

    @field_validator("occupation")
    @classmethod
    def _occ(cls, v: str) -> str:
        if v not in OCCUPATIONS:
            raise ValueError("Select an option for 'I am a'")
        return v

    @field_validator("dob")
    @classmethod
    def _dob(cls, v: str) -> str:
        try:
            d = date.fromisoformat(v)
        except ValueError:
            raise ValueError("Enter a valid date of birth")
        age = (date.today() - d).days // 365
        if age < 13 or age > 100:
            raise ValueError("Age must be between 13 and 100 years")
        return v


class RegisterIn(_ProfileFields):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Enter a valid email address")
        return v


class ProfileUpdate(_ProfileFields):
    pass


class PasswordChange(BaseModel):
    old_password: str = Field(max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(max_length=128)


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str = "user"
    phone: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    occupation: Optional[str] = None
    dob: Optional[str] = None
    created_at: Optional[str] = None
    profile_complete: bool = False


class AdminUserOut(UserOut):
    is_active: bool = True
    last_login: Optional[str] = None


class ActiveIn(BaseModel):
    active: bool


class RoleIn(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def _role(cls, v: str) -> str:
        if v not in ("user", "admin"):
            raise ValueError("Role must be user or admin")
        return v


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class AgentRequest(BaseModel):
    agent: str = Field(max_length=50)
    action: str = Field(max_length=100)
    message: str = Field(default="", max_length=30000)
    payload: dict[str, Any] = Field(default_factory=dict)


class PermissionIn(BaseModel):
    agent: str
    action: str
    permission: str


class PermissionOut(BaseModel):
    id: int
    agent: str
    action: str
    permission: str


class DocumentOut(BaseModel):
    id: int
    filename: str
    characters: int
    created_at: Optional[str] = None


class ApprovalOut(BaseModel):
    id: int
    agent: str
    action: str
    message: str
    payload: dict[str, Any]
    status: str
    created_at: Optional[str] = None


class ActivityOut(BaseModel):
    id: int
    agent: str
    action: str
    status: str
    details: str
    created_at: Optional[str] = None


class PricePoint(BaseModel):
    price: float
    at: Optional[str] = None


class ProductOut(BaseModel):
    id: int
    name: str
    url: str
    target_price: Optional[float] = None
    alert_enabled: bool
    last_price: Optional[float] = None
    currency: str
    last_checked: Optional[str] = None
    history: List[PricePoint]


class NotificationOut(BaseModel):
    id: int
    title: str
    body: str
    read: bool
    created_at: Optional[str] = None


class NotificationsOut(BaseModel):
    unread: int
    items: List[NotificationOut]
