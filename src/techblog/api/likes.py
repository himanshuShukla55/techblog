from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import func, select

from ..db import SessionDep
from ..models.likes import Like, LikeResponse
from ..utilities.blogs import get_blog_by_blog_id
from ..utilities.security import UserFromToken

likes_router = APIRouter(prefix="/blogs", tags=["blogs"])


@likes_router.post(
    "/{blog_id}/like", response_model=LikeResponse, status_code=status.HTTP_201_CREATED
)
def add_likes(session: SessionDep, user: UserFromToken, blog_id: UUID):
    blog = get_blog_by_blog_id(session, blog_id)
    new_like = Like(user_id=user.id, blog_id=blog.id)
    session.add(new_like)
    try:
        session.commit()
        session.refresh(new_like)
    except IntegrityError as _:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="user cannot like the same blog twice!",
        )
    return new_like


@likes_router.get("/{blog_id}/likes")
def get_likes_on_blog(session: SessionDep, blog_id: UUID):
    blog = get_blog_by_blog_id(session, blog_id)

    statement = select(Like.user_id, Like.created_at).where(Like.blog_id == blog.id)
    likes = session.exec(statement).all()
    return [
        {"user_id": user_id, "created_at": created_at} for user_id, created_at in likes
    ]


@likes_router.delete("/{blog_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def remove_like_on_blog(session: SessionDep, user: UserFromToken, blog_id: UUID):
    blog = get_blog_by_blog_id(session, blog_id)
    statement = select(Like).where(Like.blog_id == blog.id, Like.user_id == user.id)
    try:
        like = session.exec(statement).one()
    except NoResultFound:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized!",
        )

    session.delete(like)
    session.commit()


@likes_router.get("/{blog_id}/likes/count")
def get_likes_count_on_blog(session: SessionDep, blog_id: UUID):
    blog = get_blog_by_blog_id(session, blog_id)

    db_query = select(func.count()).select_from(Like).where(Like.blog_id == blog.id)
    count = session.exec(db_query).one()
    return {"blog_id": blog_id, "likes": count}
