from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from ..db import SessionDep
from ..models.users import CreateUser, User, UserResponse

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.post("/", response_model=UserResponse)
def add_user(session: SessionDep, data: CreateUser):
    try:
        user = User(**data.model_dump())
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except IntegrityError as _:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="account already exists with username or email!"
        )


@users_router.get("/{user_id}", response_model=UserResponse)
def get_user(session: SessionDep, user_id: UUID):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="user not found!")

    return user
