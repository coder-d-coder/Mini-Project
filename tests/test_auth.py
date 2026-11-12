import pytest

from app.models import AuthSession, User

PASSWORD = "learning2026"


def reg(email="student@example.com", password=PASSWORD, confirm=None):
    return {
        "name": "Test Student", "email": email,
        "password": password, "confirm_password": confirm or password,
    }


def test_register_normalizes_email_and_hides_secrets(client):
    r = client.post("/auth/register", json=reg("  Student@Example.COM "))
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "student@example.com"
    assert "password" not in body and "password_hash" not in body


def test_password_is_stored_as_argon2id_hash(client, db_session):
    client.post("/auth/register", json=reg())
    user = db_session.query(User).filter_by(email="student@example.com").one()
    assert user.password_hash.startswith("$argon2id$")
    assert PASSWORD not in user.password_hash


def test_duplicate_email_rejected_even_with_different_case(client):
    assert client.post("/auth/register", json=reg("a@example.com")).status_code == 201
    assert client.post("/auth/register", json=reg("A@Example.com ")).status_code == 409


@pytest.mark.parametrize("password", ["short1", "onlyletterslong", "1234567890123"])
def test_weak_passwords_rejected(client, password):
    assert client.post("/auth/register", json=reg(password=password)).status_code == 422


def test_mismatched_confirmation_rejected(client):
    r = client.post("/auth/register", json=reg(confirm="different2026"))
    assert r.status_code == 422


def test_invalid_email_rejected(client):
    assert client.post("/auth/register", json=reg("not-an-email")).status_code == 422


def test_login_failures_do_not_reveal_whether_email_exists(client):
    client.post("/auth/register", json=reg())
    wrong_pw = client.post("/auth/login", json={"email": "student@example.com", "password": "wrongpass99"})
    no_user = client.post("/auth/login", json={"email": "nobody@example.com", "password": "wrongpass99"})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json() == no_user.json()


def test_login_sets_httponly_cookie_and_me_works(client):
    client.post("/auth/register", json=reg())
    r = client.post("/auth/login", json={"email": "STUDENT@example.com", "password": PASSWORD})
    assert r.status_code == 200
    assert "csrf_token" in r.json()
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "student@example.com"


def test_logout_invalidates_session_on_the_server(client, signup_and_login, db_session):
    csrf = signup_and_login(client, "a@example.com")
    token = client.cookies.get("session")
    assert client.post("/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 204
    assert client.get("/auth/me").status_code == 401

    # Even a saved copy of the old cookie must no longer work.
    client.cookies.clear()
    replay = client.get("/auth/me", headers={"Cookie": f"session={token}"})
    assert replay.status_code == 401
    assert db_session.query(AuthSession).count() == 0


def test_logout_requires_csrf_token(client, signup_and_login):
    signup_and_login(client, "a@example.com")
    assert client.post("/auth/logout").status_code == 403
    assert client.post("/auth/logout", headers={"X-CSRF-Token": "wrong"}).status_code == 403
    assert client.get("/auth/me").status_code == 200  # still logged in


def test_lockout_after_five_failed_logins(client):
    client.post("/auth/register", json=reg())
    for _ in range(5):
        r = client.post("/auth/login", json={"email": "student@example.com", "password": "wrongpass99"})
        assert r.status_code == 401
    locked = client.post("/auth/login", json={"email": "student@example.com", "password": PASSWORD})
    assert locked.status_code == 429


def test_session_survives_new_client(client, client2, signup_and_login):
    """Accounts live in MySQL: a brand-new browser can log in to an existing account."""
    signup_and_login(client, "a@example.com")
    r = client2.post("/auth/login", json={"email": "a@example.com", "password": PASSWORD})
    assert r.status_code == 200