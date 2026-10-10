from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError

from ..db import SessionDep
from ..models.blogs import Blog, BlogResponse, CreateBlog, UpdateBlog

blogs_router = APIRouter(prefix="/blogs", tags=["blogs"])


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


@blogs_router.get("/{blog_id}", response_model=BlogResponse)
def get_blog(session: SessionDep, blog_id: UUID):
    blog = session.get(Blog, blog_id)

    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="blog not found!"
        )

    return blog


@blogs_router.patch("/{blog_id}", response_model=BlogResponse)
def update_blog(
    session: SessionDep,
    data: UpdateBlog,
    blog_id: UUID,
    author_id: UUID | None = Header(default=None),
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
def delete_blog(
    session: SessionDep, blog_id: UUID, author_id: UUID | None = Header(default=None)
):
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
