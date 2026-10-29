from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from jwt.exceptions import InvalidTokenError
from sqlalchemy.exc import NoResultFound, SQLAlchemyError

from ..db import SessionDep
from ..models.auth import LogoutRequest
from ..models.refresh_tokens import (
    RefreshToken,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from ..models.users import LoginRequest
from ..utilities.security import (
    UserFromToken,
    create_access_token,
    create_refresh_token,
    hash_token,
    save_refresh_token,
    validate_refresh_token,
    verify_password,
)
from ..utilities.users import get_user_by_email, get_user_by_user_id

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


@auth_router.post("/refresh")
def refresh_access_token(
    session: SessionDep, payload: RefreshTokenRequest
) -> RefreshTokenResponse:
    try:
        user_id, db_token = validate_refresh_token(session, payload.refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        ) from exc

    try:
        get_user_by_user_id(session, UUID(user_id))
    except HTTPException as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        ) from exc

    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    try:
        session.delete(db_token)
        session.add(RefreshToken(token_hash=hash_token(refresh_token)))
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(session: SessionDep, user: UserFromToken, payload: LogoutRequest):
    try:
        user_id, db_token = validate_refresh_token(session, payload.refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
        ) from exc

    if str(user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
        )

    try:
        session.delete(db_token)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
