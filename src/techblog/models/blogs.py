from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class CreateBlog(SQLModel):
    title: str = Field(nullable=False)
    body: str = Field(nullable=False)


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
            nullable=False,
        )
    )


class BlogResponse(Blog):
    pass
