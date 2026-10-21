from datetime import UTC, datetime, timedelta
from os import environ
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import decode, encode
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from ..db import SessionDep
from ..models.users import User
from .users import get_user_by_user_id

password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer()

JWT_SECRET_KEY = environ["JWT_SECRET_KEY"]
JWT_ALGO = "HS256"
JWT_EXP_TIME = 15

Credentials = Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]


def verify_current_user(session: SessionDep, credentials: Credentials):
    try:
        token = decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGO])
    except InvalidTokenError as _:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    if "sub" not in token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    user_id = token["sub"]
    try:
        return get_user_by_user_id(session, UUID(user_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )
        raise


UserFromToken = Annotated[User, Depends(verify_current_user)]


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(user_id: str):
    current_time = datetime.now(UTC)

    payload = {
        "sub": user_id,
        "iat": current_time,
        "exp": current_time + timedelta(minutes=JWT_EXP_TIME),
    }

    return encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGO)
