from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from ..db import SessionDep
from ..models.users import CreateUser, UpdateUser, User, UserResponse
from ..utilities.security import UserFromToken, hash_password
from ..utilities.users import get_user_by_user_id

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.post(
    "/", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def add_user(session: SessionDep, data: CreateUser):
    user_data = data.model_dump(exclude={"password"})
    user_data["hashed_password"] = hash_password(data.password)

    user = User(**user_data)
    session.add(user)

    try:
        session.commit()
        session.refresh(user)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Account already exists with username or email!",
        )
    return user


@users_router.get("/{user_id}", response_model=UserResponse)
def get_user(session: SessionDep, user_id: UUID):
    return get_user_by_user_id(session, user_id)


@users_router.patch("/update", response_model=UserResponse)
def update_user(session: SessionDep, user: UserFromToken, data: UpdateUser):
    updates = data.model_dump(exclude_unset=True)

    if "password" in updates:
        password = updates.pop("password")
        updates["hashed_password"] = hash_password(password)

    for key, value in updates.items():
        setattr(user, key, value)
    try:
        session.commit()
        session.refresh(user)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )
    return user
