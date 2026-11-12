from app.models import Job, User


def score_job(user: User, job: Job) -> dict | None:
    user_skill_names = {s.name for s in user.skills}
    job_skill_names = {s.name for s in job.skills}

    matched = user_skill_names & job_skill_names
    if not matched:
        return None

    missing = job_skill_names - user_skill_names
    skill_score = len(matched) / len(job_skill_names)

    required = job.min_experience or 0
    gap = max(0, required - (user.experience_years or 0))
    experience_score = max(0.0, 1 - gap * 0.34)  # 3+ years short = 0

    if job.location == "Remote" or (
        user.location and job.location and user.location.lower() == job.location.lower()
    ):
        location_score = 1.0
    else:
        location_score = 0.0

    total = 0.7 * skill_score + 0.2 * experience_score + 0.1 * location_score

    return {
        "job": job,
        "score": round(total * 100, 1),
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
    }


def recommend_jobs(user: User, jobs: list[Job], limit: int = 10) -> list[dict]:
    results = [r for r in (score_job(user, j) for j in jobs) if r]
    results.sort(key=lambda r: (-r["score"], r["job"].id))
    return results[:limit]