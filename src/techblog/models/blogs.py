from datetime import datetime
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class CreateBlog(SQLModel):
    title: str = Field(max_length=100)
    body: str = Field(max_length=1000)


class UpdateBlog(SQLModel):
    title: str | None = Field(default=None, max_length=100)
    body: str | None = Field(default=None, max_length=1000)

    @field_validator("title", "body")
    @classmethod
    def reject_empty_content(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Title and body cannot be empty or whitespace")
        return value


class Blog(CreateBlog, table=True):
    __tablename__ = "blogs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    author_id: UUID = Field(foreign_key="users.id", nullable=False)

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


class BlogResponse(CreateBlog):
    id: UUID
    author_id: UUID
    created_at: datetime
    updated_at: datetime


class BlogWithLikesResponse(BlogResponse):
    likes: int = Field(default=0)
