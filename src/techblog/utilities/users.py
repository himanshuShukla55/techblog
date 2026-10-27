from uuid import UUID

from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlmodel import Session, select

from ..models.users import User


def get_user_by_user_id(session: Session, user_id: UUID):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found!"
        )

    return user


def get_user_by_email(session: Session, email: EmailStr) -> User:
    db_query = select(User).where(User.email == email)
    user = session.exec(db_query).one()
    return user
