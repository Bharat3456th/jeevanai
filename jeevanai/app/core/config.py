import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parents[2]


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def _jwt_secret() -> str:
    """Use JWT_SECRET if set; otherwise create a random one once and keep it in .jwt_secret."""
    s = os.getenv("JWT_SECRET", "").strip()
    if s:
        return s
    f = BASE_DIR / ".jwt_secret"
    try:
        if f.exists():
            saved = f.read_text().strip()
            if saved:
                return saved
        s = secrets.token_urlsafe(48)
        f.write_text(s)
        return s
    except OSError:
        return secrets.token_urlsafe(48)


class Settings:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./jeevanai.db")
        self.cors_origins = [o.strip() for o in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
        self.jwt_secret = _jwt_secret()
        self.jwt_expire_minutes = _int("JWT_EXPIRE_MINUTES", 60 * 24 * 7)
        self.allow_registration = os.getenv("ALLOW_REGISTRATION", "true").lower() != "false"
        # Emails listed here (comma separated) always get the admin role.
        self.admin_emails = {e.strip().lower() for e in os.getenv("ADMIN_EMAIL", "").split(",") if e.strip()}
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.llm_model = os.getenv("LLM_MODEL", "claude-sonnet-5-5")
        self.max_upload_bytes = _int("MAX_UPLOAD_MB", 10) * 1024 * 1024
        self.price_check_minutes = _int("PRICE_CHECK_MINUTES", 60)
        self.rate_limit_per_minute = _int("RATE_LIMIT_PER_MINUTE", 30)
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = _int("SMTP_PORT", 587)
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM", "") or self.smtp_user

    # --- purane naam (alias): purani tokens.py / tests ke liye ---
    @property
    def token_minutes(self):
        return self.jwt_expire_minutes

    @token_minutes.setter
    def token_minutes(self, value):
        self.jwt_expire_minutes = value

    @property
    def secret_key(self):
        return self.jwt_secret

    @secret_key.setter
    def secret_key(self, value):
        self.jwt_secret = value


settings = Settings()
    
