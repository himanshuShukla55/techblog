from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel


class CreateLike(SQLModel):
    user_id: UUID
    blog_id: UUID


class Like(CreateLike, table=True):
    __tablename__ = "likes"

    user_id: UUID = Field(foreign_key="users.id", primary_key=True)
    blog_id: UUID = Field(foreign_key="blogs.id", primary_key=True)

    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )


class LikeResponse(CreateLike):
    created_at: datetime
