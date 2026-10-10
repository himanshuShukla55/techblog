from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import func, select

from ..db import SessionDep
from ..models.blogs import Blog, BlogResponse, CreateBlog, UpdateBlog
from ..models.likes import Like, LikeResponse
from ..models.users import User

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


@blogs_router.get("/")
def get_blogs(
    session: SessionDep,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    statement = select(Blog).limit(limit).offset(offset)
    blogs = session.exec(statement).all()

    total = session.exec(select(func.count()).select_from(Blog)).one()

    return {
        "items": blogs,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(blogs) < total,
    }


@blogs_router.post("/{blog_id}/like", response_model=LikeResponse)
def add_likes(session: SessionDep, blog_id: UUID, user_id: UUID = Header(...)):
    try:
        user = session.get(User, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="user not found!"
            )

        blog = session.get(Blog, blog_id)

        if not blog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="blog not found!"
            )

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
    
