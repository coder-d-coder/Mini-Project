import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.models import LoginAttempt

load_dotenv()

COOKIE_NAME = "session"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
SESSION_DAYS = int(os.getenv("SESSION_DAYS", "7"))

REGISTER_SCOPE = "__register__"

_hasher = PasswordHasher()  # Argon2id with library defaults
# Checked when the email doesn't exist, so response time doesn't reveal that.
DUMMY_HASH = _hasher.hash("not-a-real-password-just-for-timing")


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Only this hash is stored in MySQL, never the raw cookie value."""
    return hashlib.sha256(token.encode()).hexdigest()


# ---- attempt throttling (login failures and registrations) ----

def is_limited(db: Session, scope: str, ip: str, limit: int, minutes: int) -> bool:
    since = utcnow() - timedelta(minutes=minutes)
    count = (
        db.query(LoginAttempt)
        .filter(LoginAttempt.scope == scope, LoginAttempt.ip == ip, LoginAttempt.attempted_at > since)
        .count()
    )
    return count >= limit


def record_attempt(db: Session, scope: str, ip: str) -> None:
    db.add(LoginAttempt(scope=scope, ip=ip, attempted_at=utcnow()))
    db.commit()


def clear_attempts(db: Session, scope: str, ip: str) -> None:
    db.query(LoginAttempt).filter(LoginAttempt.scope == scope, LoginAttempt.ip == ip).delete()
    db.commit()