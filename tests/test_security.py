import hmac
from datetime import UTC, datetime, timedelta

import pytest
from jwt import decode
from jwt.exceptions import InvalidSignatureError
from sqlmodel import Session

from techblog.models.refresh_tokens import RefreshToken
from techblog.utilities.security import (
    ACCESS_JWT_SECRET_KEY,
    JWT_ALGO,
    JWT_EXP_TIME,
    REFRESH_EXP_TIME,
    REFRESH_JWT_SECRET_KEY,
    create_access_token,
    create_refresh_token,
    create_token,
    hash_password,
    hash_token,
    save_refresh_token,
    verify_password,
)


def test_plaintext_differs_from_hash():
    password = "password"

    hashed_password = hash_password(password)

    assert password != hashed_password


def test_correct_password_verifies():
    password = "password"
    hashed_password = hash_password(password)

    assert verify_password(password, hashed_password)


def test_incorrect_password_fails():
    password = "password"
    incorrect_password = "incorrect_password"
    hashed_password = hash_password(password)

    assert not verify_password(incorrect_password, hashed_password)


def test_same_password_produces_different_hashes():
    password = "password"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash)
    assert verify_password(password, second_hash)


def test_create_token():
    payload = {"user_id": 123}
    token = create_token(payload, ACCESS_JWT_SECRET_KEY)
    decode_payload = decode(token, ACCESS_JWT_SECRET_KEY, algorithms=[JWT_ALGO])
    assert decode_payload["user_id"] == payload["user_id"]


def test_create_access_token():
    user_id = "user_123"
    token = create_access_token(user_id)
    decode_payload = decode(token, ACCESS_JWT_SECRET_KEY, algorithms=[JWT_ALGO])
    assert decode_payload["sub"] == user_id
    assert decode_payload["type"] == "access"
    assert "iat" in decode_payload
    assert "exp" in decode_payload
    assert datetime.fromtimestamp(decode_payload["exp"], UTC) - datetime.fromtimestamp(
        decode_payload["iat"], UTC
    ) == timedelta(minutes=JWT_EXP_TIME)


def test_create_refresh_token():
    user_id = "user_123"
    token = create_refresh_token(user_id)
    decode_payload = decode(token, REFRESH_JWT_SECRET_KEY, algorithms=[JWT_ALGO])
    assert decode_payload["sub"] == user_id
    assert decode_payload["type"] == "refresh"
    assert "iat" in decode_payload
    assert "exp" in decode_payload
    assert datetime.fromtimestamp(decode_payload["exp"], UTC) - datetime.fromtimestamp(
        decode_payload["iat"], UTC
    ) == timedelta(days=REFRESH_EXP_TIME)


def test_other_secret_does_not_decode_token():
    user_id = "user_123"
    token = create_refresh_token(user_id)
    with pytest.raises(InvalidSignatureError):
        decode(token, ACCESS_JWT_SECRET_KEY, algorithms=[JWT_ALGO])


def test_token_hasing():
    token = "token123"
    hashed_token = hash_token(token)
    assert hmac.compare_digest(hashed_token, hash_token(token))
    assert token != hashed_token


def test_save_refresh_token(get_client_connection):
    _, connection = get_client_connection

    refresh_token = create_refresh_token("user_123")
    hashed_refresh_token = hash_token(refresh_token)
    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        save_refresh_token(session, hashed_refresh_token)
        session.flush()

        assert session.get(RefreshToken, hashed_refresh_token) is not None
