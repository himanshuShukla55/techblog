from uuid import UUID

from fastapi import HTTPException, status

from ..db import SessionDep
from ..models.blogs import Blog


def get_blog_by_blog_id(session: SessionDep, blog_id: UUID):
    blog = session.get(Blog, blog_id)

    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="blog not found!"
        )

    return blog
