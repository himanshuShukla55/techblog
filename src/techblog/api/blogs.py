from datetime import datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BeforeValidator
from sqlalchemy.exc import IntegrityError
from sqlmodel import func, select

from ..db import SessionDep
from ..models.blogs import (
    Blog,
    BlogResponse,
    BlogWithLikesResponse,
    CreateBlog,
    UpdateBlog,
)
from ..models.likes import Like
from ..utilities.blogs import get_blog_by_blog_id
from ..utilities.common import sanitise_string
from ..utilities.likes import get_likes_on_blog

blogs_router = APIRouter(prefix="/blogs", tags=["blogs"])

RequestHeader = Annotated[UUID, Header()]


@blogs_router.post("/{author_id}", response_model=BlogResponse)
def add_blog(session: SessionDep, data: CreateBlog, author_id: UUID):
    try:
        blog = Blog(**data.model_dump(), author_id=author_id)
        session.add(blog)
        session.commit()
        session.refresh(blog)
        return blog
    except IntegrityError as _:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="author not found"
        )


@blogs_router.get("/{blog_id}", response_model=BlogWithLikesResponse)
def get_blog(session: SessionDep, blog_id: UUID):
    blog = get_blog_by_blog_id(session, blog_id)
    likes = get_likes_on_blog(session, blog_id)
    return BlogWithLikesResponse(**blog.model_dump(), likes=likes)


@blogs_router.patch("/{blog_id}", response_model=BlogResponse)
def update_blog(
    session: SessionDep,
    data: UpdateBlog,
    blog_id: UUID,
    author_id: RequestHeader,
):
    blog = get_blog_by_blog_id(session, blog_id)

    if author_id != blog.author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user is forbidden to update this blog!",
        )

    updates = data.model_dump(exclude_unset=True)

    for key, value in updates.items():
        setattr(blog, key, value)

    session.commit()
    session.refresh(blog)
    return blog


@blogs_router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog(session: SessionDep, blog_id: UUID, author_id: RequestHeader):
    blog = get_blog_by_blog_id(session, blog_id)

    if author_id != blog.author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user is forbidden to delete this blog",
        )

    session.delete(blog)
    session.commit()


SearchQuery = Annotated[
    str | None, BeforeValidator(sanitise_string), Query(min_length=3, max_length=100)
]


@blogs_router.get("/")
def get_blogs(
    session: SessionDep,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
    authors_ids: Annotated[list[UUID] | None, Query()] = None,
    search: SearchQuery = None,
    created_after: Annotated[datetime | None, Query()] = None,
    created_before: Annotated[datetime | None, Query()] = None,
    min_likes: Annotated[int | None, Query(ge=0)] = None,
    has_likes: Annotated[bool | None, Query()] = None,
    sort_by: Annotated[Literal["created_at", "likes"], Query()] = "created_at",
):
    if created_before is not None and created_after is not None:
        if created_before < created_after:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="created_before cannot be less than created_after!",
            )
        elif (created_before - created_after).days > timedelta(days=365):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="difference b/w created_before and created_after cannot exceed 1 year!",
            )

    blogs_query = (
        select(Blog, func.count(Like.blog_id).label("likes"))
        .outerjoin(Like, Blog.id == Like.blog_id)
        .group_by(Blog.id)
    )

    if authors_ids is not None:
        blogs_query = blogs_query.where(Blog.author_id.in_(authors_ids))

    if search is not None:
        blogs_query = blogs_query.where(Blog.title.ilike(f"%{search}%"))

    if created_after is not None:
        blogs_query = blogs_query.where(Blog.created_at >= created_after)

    if created_before is not None:
        blogs_query = blogs_query.where(Blog.created_at <= created_before)

    if min_likes is not None:
        blogs_query = blogs_query.having(func.count(Like.blog_id) >= min_likes)

    if has_likes is not None:
        if has_likes:
            blogs_query = blogs_query.having(func.count(Like.blog_id) > 0)
        else:
            blogs_query = blogs_query.having(func.count(Like.blog_id) == 0)

    blogs_count_query = select(func.count()).select_from(blogs_query.subquery())

    blogs_query = (
        blogs_query.order_by(
            Blog.created_at.desc()
            if sort_by == "created_at"
            else func.count(Like.blog_id).desc(),
            Blog.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    blogs_response = session.exec(blogs_query).all()
    total = session.exec(blogs_count_query).one()

    items = [{**blog.model_dump(), "likes": likes} for blog, likes in blogs_response]

    next_offset = offset + len(blogs_response)
    has_more = next_offset < total
    next_offset = next_offset if has_more else None

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
        "next_offset": next_offset,
    }
