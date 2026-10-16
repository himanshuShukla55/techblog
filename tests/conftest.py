import os

import pytest
from dotenv import load_dotenv

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
