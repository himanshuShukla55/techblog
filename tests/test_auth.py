from fastapi import status
from sqlmodel import Session

from techblog.models.refresh_tokens import RefreshToken
from techblog.utilities.security import (
    decode_access_token,
    decode_refresh_token,
    hash_token,
)


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


def test_auth_token_refresh_success(get_client_connection, register_user_factory):
    client, connection = get_client_connection
    register_user = register_user_factory
    user = register_user()

    payload = {"email": "test@gmail.com", "password": "Password@1"}

    res = client.post("/auth", json=payload)

    assert res.status_code == status.HTTP_200_OK
    refresh_token = res.json().get("refresh_token")

    assert refresh_token is not None

    payload = {"refresh_token": refresh_token}

    res = client.post("/auth/refresh", json=payload)

    assert res.status_code == status.HTTP_200_OK

    body = res.json()

    assert "access_token" in body
    assert "refresh_token" in body
    assert "token_type" in body
    assert body.get("token_type") == "bearer"

    new_refresh_token = body.get("refresh_token")

    assert decode_access_token(body.get("access_token")).get("sub") == user.get("id")
    assert decode_refresh_token(new_refresh_token).get("sub") == user.get("id")

    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        assert session.get(RefreshToken, hash_token(refresh_token)) is None
        assert session.get(RefreshToken, hash_token(new_refresh_token)) is not None


def test_refresh_access_token_failed_because_refresh_hash_not_found(
    get_client_connection, register_user_factory
):
    client, connection = get_client_connection
    register_user = register_user_factory
    register_user()

    payload = {"email": "test@gmail.com", "password": "Password@1"}

    res = client.post("/auth", json=payload)

    assert res.status_code == status.HTTP_200_OK
    refresh_token = res.json().get("refresh_token")

    assert refresh_token is not None

    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        db_token = session.get(RefreshToken, hash_token(refresh_token))
        assert db_token is not None
        session.delete(db_token)
        session.commit()

    payload = {"refresh_token": refresh_token}

    res = client.post("/auth/refresh", json=payload)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json().get("detail") == "invalid token"


def test_failed_refresh_access_token_because_refresh_token_is_stale(
    get_client_connection, register_user_factory
):
    client, _ = get_client_connection
    register_user = register_user_factory

    register_user()

    payload = {"email": "test@gmail.com", "password": "Password@1"}

    res = client.post("/auth", json=payload)

    assert res.status_code == status.HTTP_200_OK

    refresh_token = res.json().get("refresh_token")
    assert refresh_token is not None

    payload = {"refresh_token": refresh_token}

    res = client.post("/auth/refresh", json=payload)

    assert res.status_code == status.HTTP_200_OK
    body = res.json()
    assert "access_token" in body
    assert "token_type" in body
    assert body.get("token_type") == "bearer"
    assert "refresh_token" in body

    res = client.post("/auth/refresh", json=payload)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json().get("detail") == "invalid token"


def test_success_logout_user(get_client_connection, register_user_factory):
    client, connection = get_client_connection
    register_user = register_user_factory

    register_user()

    payload = {"email": "test@gmail.com", "password": "Password@1"}

    res = client.post("/auth", json=payload)

    assert res.status_code == status.HTTP_200_OK
    body = res.json()
    access_token = body.get("access_token")
    refresh_token = body.get("refresh_token")

    assert access_token is not None
    assert refresh_token is not None

    auth_header = {"Authorization": f"bearer {access_token}"}
    payload = {"refresh_token": refresh_token}

    res = client.post("/auth/logout", headers=auth_header, json=payload)

    assert res.status_code == status.HTTP_204_NO_CONTENT

    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        assert session.get(RefreshToken, hash_token(refresh_token)) is None


def test_failed_logout_because_refresh_token_is_passed_in_authorization_header(
    get_client_connection, register_user_factory
):
    client, _ = get_client_connection
    register_user = register_user_factory
    register_user()

    payload = {"email": "test@gmail.com", "password": "Password@1"}

    res = client.post("/auth", json=payload)

    assert res.status_code == status.HTTP_200_OK
    refresh_token = res.json().get("refresh_token")
    assert refresh_token is not None

    auth_header = {"Authorization": f"bearer {refresh_token}"}
    payload = {"refresh_token": refresh_token}

    res = client.post("/auth/logout", headers=auth_header, json=payload)

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json().get("detail") == "Not authenticated"
