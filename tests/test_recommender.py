from types import SimpleNamespace

from app.recommender import recommend_jobs, score_job


def make_user(skills, exp=0, location=None):
    return SimpleNamespace(
        skills=[SimpleNamespace(name=s) for s in skills],
        experience_years=exp,
        location=location,
    )


def make_job(id, skills, min_exp=0, location="Remote", title="Dev"):
    return SimpleNamespace(
        id=id, title=title, min_experience=min_exp, location=location,
        skills=[SimpleNamespace(name=s) for s in skills],
    )


def test_known_score_matches_hand_calculation():
    user = make_user(["Python", "SQL", "Git"], exp=1, location="Delhi")
    job = make_job(1, ["Python", "SQL", "Git", "REST APIs"])
    result = score_job(user, job)
    assert result["score"] == 82.5  # 52.5 skills + 20 experience + 10 remote
    assert result["matched_skills"] == ["Git", "Python", "SQL"]
    assert result["missing_skills"] == ["REST APIs"]


def test_no_overlap_returns_none():
    assert score_job(make_user(["Java"]), make_job(1, ["Python"])) is None


def test_experience_gap_lowers_score():
    user = make_user(["Python", "SQL", "Git"], exp=0)
    job = make_job(1, ["Python", "SQL", "Git", "REST APIs"], min_exp=3)
    assert score_job(user, job)["score"] == 62.5  # 52.5 + 0 + 10


def test_location_match_is_case_insensitive():
    user = make_user(["Python"], location="delhi")
    same_city = score_job(user, make_job(1, ["Python"], location="Delhi"))
    other_city = score_job(user, make_job(2, ["Python"], location="Pune"))
    assert same_city["score"] - other_city["score"] == 10.0


def test_ties_are_ordered_by_job_id():
    user = make_user(["Python"])
    jobs = [make_job(5, ["Python"]), make_job(3, ["Python"])]
    assert [r["job"].id for r in recommend_jobs(user, jobs)] == [3, 5]


def test_limit_and_empty_input():
    user = make_user(["Python"])
    jobs = [make_job(i, ["Python"]) for i in range(1, 6)]
    assert len(recommend_jobs(user, jobs, limit=2)) == 2
    assert recommend_jobs(make_user([]), jobs) == []
    assert recommend_jobs(user, []) == []