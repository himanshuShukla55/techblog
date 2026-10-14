from uuid import UUID

from sqlmodel import func, select

from ..db import SessionDep
from ..models.likes import Like


def get_likes_on_blog(session: SessionDep, blog_id: UUID):
    statement = select(func.count()).select_from(Like).where(Like.blog_id == blog_id)
    likes = session.exec(statement).one()
    return likes
