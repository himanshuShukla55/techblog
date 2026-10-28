from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import NoResultFound

from ..db import SessionDep
from ..models.users import LoginRequest
from ..utilities.security import (
    create_access_token,
    create_refresh_token,
    hash_token,
    save_refresh_token,
    verify_password,
)
from ..utilities.users import get_user_by_email

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/", status_code=status.HTTP_200_OK)
def login_user(session: SessionDep, data: LoginRequest):
    try:
        user = get_user_by_email(session, data.email)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid user credentials"
        )

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid user credentials",
        )
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    refresh_token_hash = hash_token(refresh_token)
    save_refresh_token(session, refresh_token_hash)
    session.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
