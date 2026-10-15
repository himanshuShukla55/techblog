from uuid import UUID  # noqa: I001

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from ..db import SessionDep
from ..models.users import CreateUser, User, UserResponse, UpdateUser
from ..utilities.users import get_user_by_user_id
from ..utilities.security import hash_password

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.post("/", response_model=UserResponse)
def add_user(session: SessionDep, data: CreateUser):
    try:
        user_data = data.model_dump(exclude={"password"})
        user_data["hashed_password"] = hash_password(data.password)

        user = User(**user_data)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Account already exists with username or email!",
        )


@users_router.get("/{user_id}", response_model=UserResponse)
def get_user(session: SessionDep, user_id: UUID):
    return get_user_by_user_id(session, user_id)


@users_router.patch("/{user_id}/update", response_model=UserResponse)
def update_user(session: SessionDep, user_id: UUID, data: UpdateUser):
    user = get_user_by_user_id(session, user_id)
    updates = data.model_dump(exclude_unset=True)

    if "password" in updates:
        password = updates.pop("password")
        updates["hashed_password"] = hash_password(password)

    for key, value in updates.items():
        setattr(user, key, value)

    session.commit()
    session.refresh(user)
    return user
