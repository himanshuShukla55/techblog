from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import func, select

from ..db import SessionDep
from ..models.blogs import Blog
from ..models.likes import Like, LikeResponse
from ..utilities.blogs import get_blog_by_blog_id
from ..utilities.users import get_user_by_user_id

likes_router = APIRouter(prefix="/blogs", tags=["blogs"])

RequestHeader = Annotated[UUID, Header()]


@likes_router.post("/{blog_id}/like", response_model=LikeResponse)
def add_likes(session: SessionDep, blog_id: UUID, user_id: RequestHeader):
    try:
        user = get_user_by_user_id(session, user_id)

        blog = get_blog_by_blog_id(session, blog_id)

        new_like = Like(user_id=user.id, blog_id=blog.id)
        session.add(new_like)
        session.commit()
        session.refresh(new_like)
        return new_like
    except IntegrityError as _:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="user cannot like the same blog twice!",
        )


@likes_router.get("/{blog_id}/likes")
def get_likes_on_blog(session: SessionDep, blog_id: UUID):
    blog = get_blog_by_blog_id(session, blog_id)

    statement = select(Like.user_id, Like.created_at).where(
        Like.blog_id == blog.blog_id
    )
    likes = session.exec(statement).all()
    return [
        {"user_id": user_id, "created_at": created_at} for user_id, created_at in likes
    ]


@likes_router.delete("/{blog_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def remove_like_on_blog(session: SessionDep, blog_id: UUID, user_id: RequestHeader):
    try:
        blog = get_blog_by_blog_id(session, blog_id)
        statement = select(Like).where(
            Like.blog_id == blog.blog_id, Like.user_id == user_id
        )

        like = session.exec(statement).one()

        session.delete(like)
        session.commit()
    except NoResultFound as _:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no like by user found on blog!",
        )


@likes_router.get("/{blog_id}/likes/count")
def get_likes_count_on_blog(session: SessionDep, blog_id: UUID):
    blog = get_blog_by_blog_id(session, blog_id)

    db_query = (
        select(func.count()).select_from(Like).where(Like.blog_id == blog.blog_id)
    )
    count = session.exec(db_query).one()
    return {"blog_id": blog_id, "likes": count}
