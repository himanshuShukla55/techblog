from datetime import datetime
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class CreateUser(SQLModel):
    username: str = Field(nullable=False, unique=True)

    email: EmailStr = Field(
        unique=True,
        nullable=False,
    )


class User(CreateUser, table=True):
    __tablename__ = "users"
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        nullable=False,
    )

    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )


class UserResponse(User):
    pass
