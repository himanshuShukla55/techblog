from datetime import datetime
from uuid import UUID, uuid4

from pydantic import ConfigDict, field_validator, model_validator
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class CreateBlog(SQLModel):
    title: str = Field(max_length=100)
    body: str = Field(max_length=1000)


class UpdateBlog(SQLModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, max_length=100)
    body: str | None = Field(default=None, max_length=1000)

    @field_validator("title", "body")
    @classmethod
    def reject_empty_content(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Title and body cannot be empty or whitespace")
        return value

    @model_validator(mode="after")
    def validate_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("Update body cannot be empty!")
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")

        return self


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
