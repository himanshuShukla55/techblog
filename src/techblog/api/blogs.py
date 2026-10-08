from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from ..db import SessionDep
from ..models.blogs import Blog, BlogResponse, CreateBlog

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
        raise HTTPException(status_code=404, detail="author not found")


@blogs_router.get("/{blog_id}", response_model=BlogResponse)
def get_blog(session: SessionDep, blog_id: UUID):
    blog = session.get(Blog, blog_id)

    if not blog:
        raise HTTPException(status_code=404, detail="blog not found!")

    return blog
