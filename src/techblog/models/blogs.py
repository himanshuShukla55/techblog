from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class CreateBlog(SQLModel):
    title: str = Field(nullable=False, max_length=100)
    body: str = Field(nullable=False, max_length=1000)


class Blog(CreateBlog, table=True):
    __tablename__ = "blogs"

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)

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


class BlogResponse(Blog):
    pass


class UpdateBlog(SQLModel):
    title: str | None = Field(default=None, max_length=100)
    body: str | None = Field(default=None, max_length=1000)
