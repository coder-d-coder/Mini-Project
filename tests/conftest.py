import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from app import models
from app.database import Base, get_db
from app.main import app

load_dotenv()

TEST_DB = "job_recommender_test"
PASSWORD = "learning2026"


def _url(database=None):
    return URL.create(
        "mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=database,
        query={"charset": "utf8mb4"},
    )


@pytest.fixture(scope="session")
def test_engine():
    assert TEST_DB.endswith("_test"), "Refusing to run tests on a non-test database"

    admin = create_engine(_url(), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {TEST_DB} CHARACTER SET utf8mb4"))
    admin.dispose()

    engine = create_engine(_url(TEST_DB), pool_pre_ping=True)
    assert engine.url.database == TEST_DB
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def session_factory(test_engine):
    return sessionmaker(bind=test_engine, autoflush=False)


@pytest.fixture
def db_session(test_engine, session_factory):
    """Empties every test table, then seeds 6 skills and 2 jobs (ids restart at 1)."""
    assert test_engine.url.database == TEST_DB
    with test_engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in Base.metadata.sorted_tables:
            conn.execute(text(f"TRUNCATE TABLE `{table.name}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    session = session_factory()
    skills = {n: models.Skill(name=n) for n in ["Python", "SQL", "Git", "REST APIs", "HTML", "CSS"]}
    session.add_all(skills.values())
    session.flush()
    session.add(models.Job(
        title="Junior Python Developer", company="CodeNest", location="Remote",
        min_experience=0, salary_min=300000, salary_max=500000,
        skills=[skills[n] for n in ["Python", "SQL", "Git", "REST APIs"]],
    ))
    session.add(models.Job(
        title="Frontend Developer", company="PixelPath", location="Remote",
        min_experience=1, salary_min=500000, salary_max=900000,
        skills=[skills[n] for n in ["HTML", "CSS"]],
    ))
    session.commit()
    yield session
    session.close()


@pytest.fixture
def override_db(db_session, session_factory):
    def _get_db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def client2(override_db):
    """A second browser with its own cookie jar."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def signup_and_login():
    """Returns a function: (client, email) -> csrf token."""
    def _do(client, email):
        r = client.post("/auth/register", json={
            "name": "Test Student", "email": email,
            "password": PASSWORD, "confirm_password": PASSWORD,
        })
        assert r.status_code == 201, r.text
        r = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        assert r.status_code == 200, r.text
        return r.json()["csrf_token"]
    return _do