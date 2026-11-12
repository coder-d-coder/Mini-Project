from datetime import datetime

import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from app.data.roles import ROLES

class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    company: str
    location: str | None = None
    description: str | None = None
    min_experience: int | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    skills: list[SkillOut] = []


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    location: str | None = None
    experience_years: int = Field(default=0, ge=0)
    skills: list[str] = []  # skill names, e.g. ["Python", "SQL"]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    location: str | None = None
    experience_years: int | None = None
    skills: list[SkillOut] = []


class RecommendationOut(BaseModel):
    job: JobOut
    score: float
    matched_skills: list[str]
    missing_skills: list[str]

class UserUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    location: str | None = None
    experience_years: int = Field(default=0, ge=0)
    skills: list[str] = []

class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(max_length=128)
    confirm_password: str

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("Full name is required.")
        return v

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters.")
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("Password must include at least one letter and one number.")
        return v

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class LoginIn(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    location: str | None = None
    experience_years: int | None = None
    target_role: str | None = None


class AuthResponse(BaseModel):
    user: AccountOut
    csrf_token: str


class ProfileOut(AccountOut):
    skills: list[SkillOut] = []


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    location: str | None = Field(default=None, max_length=100)
    experience_years: int = Field(default=0, ge=0, le=50)
    target_role: str | None = None
    skills: list[str] = Field(default=[], max_length=60)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("Full name is required.")
        return v

    @field_validator("location")
    @classmethod
    def clean_location(cls, v):
        v = (v or "").strip()
        return v or None

    @field_validator("target_role")
    @classmethod
    def check_role(cls, v):
        if not v:
            return None
        if v not in ROLES:
            raise ValueError("Unknown target role.")
        return v


class DashboardRecommendationOut(RecommendationOut):
    role_match: bool = False


class ResourceOut(BaseModel):
    title: str
    url: str
    kind: str


class SkillGapItem(BaseModel):
    skill: str
    needed_by: int
    resources: list[ResourceOut] = []


class SkillGapOut(BaseModel):
    role: str | None
    based_on_jobs: int
    gaps: list[SkillGapItem]

class SavedJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job: JobOut
    created_at: datetime