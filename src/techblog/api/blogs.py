from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, status
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
    blog = session.get(Blog, blog_id)

    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="blog not found!"
        )

    statement = select(func.count()).select_from(Like).where(Like.blog_id == blog.id)
    likes = session.exec(statement).one()
    return BlogWithLikesResponse(**blog.model_dump(), likes=likes)


@blogs_router.patch("/{blog_id}", response_model=BlogResponse)
def update_blog(
    session: SessionDep,
    data: UpdateBlog,
    blog_id: UUID,
    author_id: RequestHeader,
):
    blog = session.get(Blog, blog_id)

    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="blog not found!"
        )

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
    blog = session.get(Blog, blog_id)

    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="blog not found!"
        )

    if author_id != blog.author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user is forbidden to delete this blog",
        )

    session.delete(blog)
    session.commit()


@blogs_router.get("/")
def get_blogs(
    session: SessionDep,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    author_id: Annotated[UUID | None, Query()] = None,
):
    blogs_query = (
        select(Blog, func.count(Like.blog_id).label("likes"))
        .outerjoin(Like, Blog.id == Like.blog_id)
        .group_by(Blog.id)
        .limit(limit)
        .offset(offset)
    )

    blogs_count_query = select(func.count()).select_from(Blog)


    if author_id is not None:
        blogs_query = blogs_query.where(Blog.author_id == author_id)
        blogs_count_query = blogs_count_query.where(Blog.author_id == author_id)

    blogsWithLikesCount = session.exec(blogs_query).all()

    total = session.exec(blogs_count_query).one()

    items = [
        {**blog.model_dump(), "likes": likes} for blog, likes in blogsWithLikesCount
    ]

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(blogsWithLikesCount) < total,
    }
