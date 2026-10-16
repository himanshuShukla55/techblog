from fastapi import status
from sqlmodel import Session, select

from techblog.models.users import User
from techblog.utilities.security import verify_password


def test_user_registration(test_client):
    client, connection = test_client

    password = "password@1"

    payload = {
        "username": "test user",
        "email": "test_user@gmail.com",
        "password": password,
    }

    response = client.post("/users", json=payload)

    assert response.status_code == status.HTTP_201_CREATED

    body = response.json()

    assert {"id", "username", "email", "created_at"} <= body.keys()
    assert body["username"] == payload["username"]
    assert body["email"] == payload["email"]
    assert "password" not in body
    assert "hashed_password" not in body

    with Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    ) as session:
        user = session.exec(select(User).where(User.email == payload["email"])).one()

        assert user.hashed_password != password
        assert verify_password(password, user.hashed_password)


def test_fail_user_register_with_existing_email(test_client):
    client, connection = test_client

    payload_first_user = {
        "username": "test_user_one",
        "email": "test_user@gmail.com",
        "password": "password",
    }
    response_one = client.post("/users", json=payload_first_user)

    assert response_one.status_code == status.HTTP_201_CREATED

    payload_second_user = {
        "username": "test_user_two",
        "email": "test_user@gmail.com",
        "password": "password",
    }

    response_two = client.post("/users", json=payload_second_user)
    assert response_two.status_code == status.HTTP_409_CONFLICT

    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        users_query = select(User).where(User.email == "test_user@gmail.com")
        result = session.exec(users_query).all()
        assert len(result) == 1


def test_fail_duplicate_username_register(test_client):
    client, connection = test_client

    payload_user_one = {
        "username": "test user",
        "email": "test_one@gmail.com",
        "password": "password",
    }

    response = client.post("/users", json=payload_user_one)
    assert response.status_code == status.HTTP_201_CREATED

    payload_user_two = {
        "username": "test user",
        "email": "test_two@gmail.com",
        "password": "password",
    }

    response = client.post("/users", json=payload_user_two)
    assert response.status_code == status.HTTP_409_CONFLICT

    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        users_query = select(User).where(User.username == "test user")
        result = session.exec(users_query).all()
        assert len(result) == 1
