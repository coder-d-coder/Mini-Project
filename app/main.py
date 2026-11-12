from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models  # noqa: F401  (needed so tables are registered)
from app.database import Base, engine, get_db
from app.routers import auth, jobs, me, skills

app = FastAPI(title="Smart Job Recommendation System")

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(me.router)
app.include_router(jobs.router)
app.include_router(skills.router)


@app.get("/")
def root():
    return {"message": "Smart Job Recommendation System API"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT DATABASE()")).scalar()
    return {"connected_to": result}


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")