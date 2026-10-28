import hashlib
from datetime import UTC, datetime, timedelta
from os import environ
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import decode, encode
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlmodel import Session

from ..db import SessionDep
from ..models.refresh_tokens import RefreshToken
from ..models.users import User
from .users import get_user_by_user_id

password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer()

ACCESS_JWT_SECRET_KEY = environ["ACCESS_JWT_SECRET_KEY"]
REFRESH_JWT_SECRET_KEY = environ["REFRESH_JWT_SECRET_KEY"]
JWT_ALGO = "HS256"
JWT_EXP_TIME = 15
REFRESH_EXP_TIME = 7

Credentials = Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]


def verify_current_user(session: SessionDep, credentials: Credentials):
    try:
        token = decode_access_token(credentials.credentials)
    except InvalidTokenError as _:
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


def create_token(payload: dict, secret: str) -> str:
    return encode(payload, secret, algorithm=JWT_ALGO)


def create_access_token(user_id: str) -> str:
    current_time = datetime.now(UTC)

    payload = {
        "sub": user_id,
        "type": "access",
        "iat": current_time,
        "exp": current_time + timedelta(minutes=JWT_EXP_TIME),
    }

    return create_token(payload, ACCESS_JWT_SECRET_KEY)


def create_refresh_token(user_id: str) -> str:
    current_time = datetime.now(UTC)
    payload = {
        "jti": str(uuid4()),
        "sub": user_id,
        "type": "refresh",
        "iat": current_time,
        "exp": current_time + timedelta(days=REFRESH_EXP_TIME),
    }

    return create_token(payload, REFRESH_JWT_SECRET_KEY)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def save_refresh_token(session: Session, token_hash: str):
    refresh_token = RefreshToken(token_hash=token_hash)
    session.add(refresh_token)


def decode_token(token: str, secret: str, token_type: str) -> dict:
    payload = decode(token, secret, algorithms=[JWT_ALGO])
    if payload.get("type") != token_type:
        raise InvalidTokenError("Invalid token type")

    user_id = payload.get("sub", None)

    if not user_id or not isinstance(user_id, str):
        raise InvalidTokenError("invalid token sub")

    try:
        UUID(user_id)
    except ValueError:
        raise InvalidTokenError("invalid token sub")

    return payload


def decode_access_token(token:str) -> dict:
    return decode_token(token, ACCESS_JWT_SECRET_KEY, "access")


def decode_refresh_token(token:str) -> dict:
    return decode_token(token, REFRESH_JWT_SECRET_KEY, "refresh")


def validate_refresh_token(session: Session, token: str) -> str:
    payload = decode_refresh_token(token)

    hashed_token = hash_token(token)
    db_token = session.get(RefreshToken, hashed_token)

    if not db_token:
        raise InvalidTokenError("invalid token")

    return payload["sub"]
