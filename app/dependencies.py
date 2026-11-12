import secrets

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuthSession, User
from app.security import COOKIE_NAME, hash_token, utcnow


def get_current_session(request: Request, db: Session = Depends(get_db)) -> AuthSession:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = db.query(AuthSession).filter(AuthSession.token_hash == hash_token(token)).first()
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if session.expires_at < utcnow():
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=401, detail="Session expired")
    return session


def get_current_user(session: AuthSession = Depends(get_current_session)) -> User:
    return session.user


def require_csrf(
    session: AuthSession = Depends(get_current_session),
    x_csrf_token: str | None = Header(default=None),
) -> None:
    """Use on every POST/PUT/DELETE that needs a logged-in user."""
    if not x_csrf_token or not secrets.compare_digest(x_csrf_token, session.csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")