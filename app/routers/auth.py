from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_session, get_current_user, require_csrf
from app.models import AuthSession, User
from app.schemas import AccountOut, AuthResponse, LoginIn, RegisterIn
from app.security import (
    COOKIE_NAME,
    COOKIE_SECURE,
    DUMMY_HASH,
    REGISTER_SCOPE,
    SESSION_DAYS,
    clear_attempts,
    hash_password,
    hash_token,
    is_limited,
    new_token,
    normalize_email,
    record_attempt,
    utcnow,
    verify_password,
)
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_FAILED_LOGINS = 5
LOGIN_WINDOW_MIN = 15
MAX_REGISTRATIONS = 10
REGISTER_WINDOW_MIN = 60


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=AccountOut, status_code=201)
def register(payload: RegisterIn, request: Request, db: Session = Depends(get_db)):
    ip = client_ip(request)
    if is_limited(db, REGISTER_SCOPE, ip, MAX_REGISTRATIONS, REGISTER_WINDOW_MIN):
        raise HTTPException(status_code=429, detail="Too many sign-up attempts. Try again later.")
    record_attempt(db, REGISTER_SCOPE, ip)

    email = normalize_email(payload.email)
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(
        name=payload.name,
        email=email,
        password_hash=hash_password(payload.password),
        experience_years=0,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # two requests raced past the check above
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    db.refresh(user)
    return user


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)
    ip = client_ip(request)

    if is_limited(db, email, ip, MAX_FAILED_LOGINS, LOGIN_WINDOW_MIN):
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in 15 minutes.")

    user = db.query(User).filter(User.email == email).first()
    # Always run one hash check so unknown emails take about as long as real ones.
    password_ok = verify_password(user.password_hash if user else DUMMY_HASH, payload.password)

    if not user or not password_ok:
        record_attempt(db, email, ip)
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    clear_attempts(db, email, ip)
    db.query(AuthSession).filter(
        AuthSession.user_id == user.id, AuthSession.expires_at < utcnow()
    ).delete()

    token = new_token()
    csrf = new_token()
    db.add(
        AuthSession(
            token_hash=hash_token(token),
            user_id=user.id,
            csrf_token=csrf,
            expires_at=utcnow() + timedelta(days=SESSION_DAYS),
        )
    )
    db.commit()

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_DAYS * 86400,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return {"user": user, "csrf_token": csrf}


@router.post("/logout", status_code=204, dependencies=[Depends(require_csrf)])
def logout(session: AuthSession = Depends(get_current_session), db: Session = Depends(get_db)):
    db.delete(session)
    db.commit()
    response = Response(status_code=204)
    response.delete_cookie(COOKIE_NAME, path="/")
    return response


@router.get("/me", response_model=AuthResponse)
def me(session: AuthSession = Depends(get_current_session), user: User = Depends(get_current_user)):
    return {"user": user, "csrf_token": session.csrf_token}