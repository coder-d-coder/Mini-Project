from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base

user_skills = Table(
    "user_skills",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

job_skills = Table(
    "job_skills",
    Base.metadata,
    Column("job_id", Integer, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    location = Column(String(100))
    experience_years = Column(Integer, default=0)
    password_hash = Column(String(255), nullable=False)
    target_role = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    skills = relationship("Skill", secondary=user_skills, back_populates="users")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    company = Column(String(200), nullable=False)
    location = Column(String(100))
    description = Column(Text)
    min_experience = Column(Integer, default=0)
    salary_min = Column(Numeric(10, 2))
    salary_max = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

    skills = relationship("Skill", secondary=job_skills, back_populates="jobs")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    users = relationship("User", secondary=user_skills, back_populates="skills")
    jobs = relationship("Job", secondary=job_skills, back_populates="skills")


class AuthSession(Base):
    __tablename__ = "sessions"

    token_hash = Column(String(64), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    csrf_token = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User")


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True)
    scope = Column(String(255), nullable=False)  # the email, or "__register__"
    ip = Column(String(45), nullable=False)
    attempted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("ix_attempts_lookup", "scope", "ip", "attempted_at"),)

class SavedJob(Base):
    __tablename__ = "saved_jobs"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    job = relationship("Job")