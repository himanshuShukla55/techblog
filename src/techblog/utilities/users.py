from uuid import UUID

from fastapi import HTTPException, status

from ..db import SessionDep
from ..models.users import User


def get_user_by_user_id(session: SessionDep, user_id: UUID):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found!"
        )

    return user
