from fastapi import status

from techblog.utilities.security import (
    decode_access_token,
    decode_refresh_token,
    hash_token,
)

from sqlmodel import Session

from techblog.models.refresh_tokens import RefreshToken


def test_login_success(get_client_connection, register_user_factory):
    client, connection = get_client_connection
    register_user = register_user_factory

    user = register_user()

    payload = {"email": "test@gmail.com", "password": "Password@1"}

    response = client.post("/auth", json=payload)

    assert response.status_code == status.HTTP_200_OK
    body = response.json()

    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"

    decoded_access_token = decode_access_token(body["access_token"])
    decoded_refresh_token = decode_refresh_token(body["refresh_token"])
    assert decoded_access_token["sub"] == user["id"]
    assert decoded_refresh_token["sub"] == user["id"]

    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        assert session.get(RefreshToken, hash_token(body["refresh_token"])) is not None


def test_failed_login_due_to_wrong_email(get_client_connection, register_user_factory):
    client, _ = get_client_connection
    register_user = register_user_factory

    register_user()

    payload = {"email": "testuser@gmail.com", "password": "Password@1"}

    response = client.post("/auth", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body["detail"] == "invalid user credentials"


def test_failed_login_due_to_wrong_password(
    get_client_connection, register_user_factory
):
    client, _ = get_client_connection
    register_user = register_user_factory

    register_user()

    payload = {"email": "test@gmail.com", "password": "Passwor"}

    response = client.post("/auth", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body["detail"] == "invalid user credentials"
