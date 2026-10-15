from datetime import datetime
from uuid import UUID, uuid4

from pydantic import EmailStr, field_validator
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class BaseUser(SQLModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr


class CreateUser(BaseUser):
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password cannot be empty or whitespace")

        return value


class UpdateUser(SQLModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)

    @field_validator("username", "password")
    @classmethod
    def strip_whitespace(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class User(BaseUser, table=True):
    __tablename__ = "users"

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


class UserResponse(BaseUser):
    id: UUID
    created_at: datetime
