"""Password hashing and JWT (HS256) using only the standard library."""
import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional
from app.core.config import settings

ITERATIONS = 200_000


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt, dk = stored.split("$")
        calc = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iters))
        return hmac.compare_digest(calc.hex(), dk)
    except (ValueError, AttributeError):
        return False


def _sign(msg: str) -> str:
    return _b64(hmac.new(settings.jwt_secret.encode(), msg.encode(), hashlib.sha256).digest())


def create_token(user_id: int) -> str:
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub": str(user_id), "exp": int(time.time()) + settings.token_minutes * 60},
                              separators=(",", ":")).encode())
    return f"{header}.{payload}.{_sign(header + '.' + payload)}"


def decode_token(token: str) -> Optional[int]:
    try:
        header, payload, sig = token.split(".")
        if not hmac.compare_digest(_sign(header + "." + payload), sig):
            return None
        data = json.loads(_unb64(payload))
        if data["exp"] < time.time():
            return None
        return int(data["sub"])
    except (ValueError, KeyError, TypeError):
        return None
