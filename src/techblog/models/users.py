from datetime import datetime
from uuid import UUID, uuid4

from pydantic import EmailStr, field_validator
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


def normalize_username(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


def validate_password(value: str) -> str:
    if not value.strip():
        raise ValueError("Password cannot be empty or whitespace")
    return value


class UserBase(SQLModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr

    @field_validator("username", mode="before")
    @classmethod
    def clean_username(cls, value: object) -> object:
        return normalize_username(value)


class CreateUser(UserBase):
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password(value)


class UpdateUser(SQLModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)

    @field_validator("username", mode="before")
    @classmethod
    def clean_username(cls, value: object) -> object:
        return normalize_username(value)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str | None) -> str | None:
        return validate_password(value) if value is not None else None


class User(UserBase, table=True):
    __tablename__ = "users"

    username: str = Field(min_length=3, max_length=50, unique=True)
    email: EmailStr = Field(unique=True)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    hashed_password: str = Field(nullable=False)

    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )
    )


class UserResponse(UserBase):
    id: UUID
    created_at: datetime


class LoginRequest(SQLModel):
    email: EmailStr
    password: str = Field(min_length=1)
