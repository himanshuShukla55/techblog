import os

import pytest
from dotenv import load_dotenv
from fastapi import status

load_dotenv(".env.test", override=True)

database_url = os.getenv("DATABASE_URL", "")

if not database_url.endswith("/techblog_test"):
    raise RuntimeError("Tests must use the techblog_test database")


@pytest.fixture
def test_client():
    from fastapi.testclient import TestClient
    from sqlmodel import Session

    from techblog.db import engine, get_db
    from techblog.main import app

    if engine.url.database != "techblog_test":
        raise RuntimeError("Refusing to run tests against a non-test database")

    connection = engine.connect()
    transaction = connection.begin()

    def override_get_db():
        with Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
        ) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client, connection
    finally:
        app.dependency_overrides.pop(get_db, None)
        transaction.rollback()
        connection.close()


@pytest.fixture
def register_user_factory(test_client):
    client, _ = test_client

    def register_user(
        username="test_user", email="test@gmail.com", password="Password@1"
    ):

        payload = {
            "username": username,
            "email": email,
            "password": password,
        }

        res = client.post("/users", json=payload)

        assert res.status_code == status.HTTP_201_CREATED
        return payload

    return register_user


@pytest.fixture
def test_auth(test_client, register_user_factory):
    client, _ = test_client
    register_user = register_user_factory
    payload = register_user()

    def authenticate_user(user=payload):

        res = client.post(
            "/auth", json={"email": user["email"], "password": user["password"]}
        )

        assert res.status_code == status.HTTP_200_OK
        token = res.json()["access_token"]

        return {"Authorization": f"Bearer {token}"}

    return authenticate_user
