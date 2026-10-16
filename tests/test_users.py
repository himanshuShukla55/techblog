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
