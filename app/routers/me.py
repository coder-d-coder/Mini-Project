from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import Job, SavedJob, Skill, User

from app.data.resources import resources_for
from app.data.roles import ROLES, role_matches
from app.database import get_db
from app.dependencies import get_current_user, require_csrf
from app.models import Job, Skill, User
from app.recommender import recommend_jobs
from app.schemas import (
    DashboardRecommendationOut,
    ProfileOut,
    ProfileUpdate,
    SkillGapOut,
    SavedJobOut,
)

router = APIRouter(prefix="/me", tags=["me"])


def _check_role(role: str | None) -> str | None:
    if role and role not in ROLES:
        raise HTTPException(status_code=400, detail="Unknown target role.")
    return role or None


def _ranked(db: Session, user: User, role: str | None, limit: int) -> list[dict]:
    jobs = db.query(Job).options(selectinload(Job.skills)).all()
    ranked = recommend_jobs(user, jobs, limit=max(len(jobs), 1))
    for r in ranked:
        r["role_match"] = bool(role) and role_matches(role, r["job"].title)
    if role:
        ranked.sort(key=lambda r: not r["role_match"])  # stable: keeps score order inside each group
    return ranked[:limit]


@router.get("/roles")
def list_roles(user: User = Depends(get_current_user)):
    return list(ROLES.keys())


@router.get("/profile", response_model=ProfileOut)
def get_profile(user: User = Depends(get_current_user)):
    return user


@router.put("/profile", response_model=ProfileOut, dependencies=[Depends(require_csrf)])
def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    found, missing = {}, []
    for name in payload.skills:
        skill = db.query(Skill).filter(Skill.name == name.strip()).first()
        if skill:
            found[skill.id] = skill
        else:
            missing.append(name)
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown skills: {missing}")

    user.name = payload.name
    user.location = payload.location
    user.experience_years = payload.experience_years
    user.target_role = payload.target_role
    user.skills = list(found.values())
    db.commit()
    db.refresh(user)
    return user


@router.get("/recommendations", response_model=list[DashboardRecommendationOut])
def my_recommendations(
    role: str | None = None,
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    role = _check_role(role if role is not None else user.target_role)
    limit = min(max(limit, 1), 50)
    return _ranked(db, user, role, limit)


@router.get("/skill-gap", response_model=SkillGapOut)
def my_skill_gap(
    role: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    role = _check_role(role if role is not None else user.target_role)
    ranked = _ranked(db, user, role, 50)
    pool = [r for r in ranked if r["role_match"]] if role else ranked
    pool = pool[:10]

    counts = Counter()
    for r in pool:
        counts.update(r["missing_skills"])
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:5]

    return {
        "role": role,
        "based_on_jobs": len(pool),
        "gaps": [
            {"skill": name, "needed_by": n, "resources": resources_for(name)}
            for name, n in top
        ],
    }

@router.get("/saved-jobs", response_model=list[SavedJobOut])
def list_saved_jobs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(SavedJob)
        .options(selectinload(SavedJob.job).selectinload(Job.skills))
        .filter(SavedJob.user_id == user.id)
        .order_by(SavedJob.created_at.desc())
        .all()
    )


@router.post("/saved-jobs/{job_id}", status_code=201, dependencies=[Depends(require_csrf)])
def save_job(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not db.query(Job.id).filter(Job.id == job_id).first():
        raise HTTPException(status_code=404, detail="Job not found")
    exists = db.query(SavedJob).filter(SavedJob.user_id == user.id, SavedJob.job_id == job_id).first()
    if not exists:
        db.add(SavedJob(user_id=user.id, job_id=job_id))
        try:
            db.commit()
        except IntegrityError:  # a double click raced past the check above
            db.rollback()
    return {"job_id": job_id, "saved": True}


@router.delete("/saved-jobs/{job_id}", status_code=204, dependencies=[Depends(require_csrf)])
def unsave_job(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(SavedJob).filter(SavedJob.user_id == user.id, SavedJob.job_id == job_id).delete()
    db.commit()