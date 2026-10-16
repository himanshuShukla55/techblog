from uuid import UUID

from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlmodel import select

from ..db import SessionDep
from ..models.users import User


def get_user_by_user_id(session: SessionDep, user_id: UUID):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found!"
        )

    return user


def get_user_by_email(session: SessionDep, email: EmailStr) -> User:
    db_query = select(User).where(User.email == email)
    user = session.exec(db_query).one()
    return user
