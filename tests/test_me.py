import pytest

PROFILE = {
    "name": "Test Student", "location": "Delhi", "experience_years": 1,
    "target_role": "Backend Developer", "skills": ["Python", "SQL", "Git"],
}


def csrf_headers(token):
    return {"X-CSRF-Token": token}


@pytest.mark.parametrize("method,path", [
    ("get", "/me/profile"),
    ("get", "/me/roles"),
    ("get", "/me/recommendations"),
    ("get", "/me/skill-gap"),
    ("get", "/me/saved-jobs"),
    ("post", "/me/saved-jobs/1"),
    ("delete", "/me/saved-jobs/1"),
    ("put", "/me/profile"),
])
def test_protected_endpoints_reject_anonymous_requests(client, method, path):
    kwargs = {"json": PROFILE} if method == "put" else {}
    assert getattr(client, method)(path, **kwargs).status_code == 401


# ---------- profile ----------

def test_profile_update_persists_for_a_new_login(client, client2, signup_and_login):
    csrf = signup_and_login(client, "a@example.com")
    r = client.put("/me/profile", json=PROFILE, headers=csrf_headers(csrf))
    assert r.status_code == 200

    client2.post("/auth/login", json={"email": "a@example.com", "password": "learning2026"})
    data = client2.get("/me/profile").json()
    assert data["location"] == "Delhi"
    assert data["target_role"] == "Backend Developer"
    assert sorted(s["name"] for s in data["skills"]) == ["Git", "Python", "SQL"]
    assert "password_hash" not in data


def test_profile_update_requires_csrf(client, signup_and_login):
    signup_and_login(client, "a@example.com")
    assert client.put("/me/profile", json=PROFILE).status_code == 403


def test_profile_rejects_unknown_skill_and_role(client, signup_and_login):
    csrf = signup_and_login(client, "a@example.com")
    bad_skill = {**PROFILE, "skills": ["Python", "Underwater Basket Weaving"]}
    assert client.put("/me/profile", json=bad_skill, headers=csrf_headers(csrf)).status_code == 400
    bad_role = {**PROFILE, "target_role": "Astronaut"}
    assert client.put("/me/profile", json=bad_role, headers=csrf_headers(csrf)).status_code == 422


def test_users_cannot_see_each_others_profiles(client, client2, signup_and_login):
    csrf_a = signup_and_login(client, "a@example.com")
    signup_and_login(client2, "b@example.com")
    client.put("/me/profile", json=PROFILE, headers=csrf_headers(csrf_a))
    other = client2.get("/me/profile").json()
    assert other["email"] == "b@example.com"
    assert other["skills"] == []


# ---------- recommendations ----------

def test_recommendations_use_the_existing_engine(client, signup_and_login):
    csrf = signup_and_login(client, "a@example.com")
    client.put("/me/profile", json=PROFILE, headers=csrf_headers(csrf))
    recs = client.get("/me/recommendations").json()
    assert len(recs) == 1  # the frontend job shares no skills
    top = recs[0]
    assert top["job"]["title"] == "Junior Python Developer"
    assert top["score"] == 82.5
    assert top["matched_skills"] == ["Git", "Python", "SQL"]
    assert top["missing_skills"] == ["REST APIs"]
    assert top["role_match"] is True


def test_unknown_role_in_query_is_rejected(client, signup_and_login):
    signup_and_login(client, "a@example.com")
    assert client.get("/me/recommendations", params={"role": "Astronaut"}).status_code == 400


def test_skill_gap_lists_missing_skills_with_resources(client, signup_and_login):
    csrf = signup_and_login(client, "a@example.com")
    client.put("/me/profile", json=PROFILE, headers=csrf_headers(csrf))
    gap = client.get("/me/skill-gap").json()
    assert [g["skill"] for g in gap["gaps"]] == ["REST APIs"]
    assert gap["gaps"][0]["needed_by"] == 1
    assert len(gap["gaps"][0]["resources"]) >= 1


# ---------- saved jobs ----------

def test_save_list_and_remove_job(client, signup_and_login):
    csrf = signup_and_login(client, "a@example.com")
    h = csrf_headers(csrf)
    assert client.post("/me/saved-jobs/1", headers=h).status_code == 201
    assert client.post("/me/saved-jobs/1", headers=h).status_code == 201  # repeat is safe

    saved = client.get("/me/saved-jobs").json()
    assert len(saved) == 1
    assert saved[0]["job"]["id"] == 1

    assert client.delete("/me/saved-jobs/1", headers=h).status_code == 204
    assert client.get("/me/saved-jobs").json() == []


def test_saving_unknown_job_returns_404(client, signup_and_login):
    csrf = signup_and_login(client, "a@example.com")
    assert client.post("/me/saved-jobs/999", headers=csrf_headers(csrf)).status_code == 404


def test_saved_job_changes_require_csrf(client, signup_and_login):
    signup_and_login(client, "a@example.com")
    assert client.post("/me/saved-jobs/1").status_code == 403
    assert client.delete("/me/saved-jobs/1").status_code == 403


def test_saved_jobs_are_private_to_each_user(client, client2, signup_and_login):
    csrf_a = signup_and_login(client, "a@example.com")
    csrf_b = signup_and_login(client2, "b@example.com")

    client.post("/me/saved-jobs/1", headers=csrf_headers(csrf_a))
    assert client2.get("/me/saved-jobs").json() == []

    # B "removing" job 1 must not remove A's saved job.
    assert client2.delete("/me/saved-jobs/1", headers=csrf_headers(csrf_b)).status_code == 204
    assert len(client.get("/me/saved-jobs").json()) == 1


def test_saved_jobs_persist_across_logins(client, client2, signup_and_login):
    csrf = signup_and_login(client, "a@example.com")
    client.post("/me/saved-jobs/2", headers=csrf_headers(csrf))
    client2.post("/auth/login", json={"email": "a@example.com", "password": "learning2026"})
    assert [s["job"]["id"] for s in client2.get("/me/saved-jobs").json()] == [2]