from fastapi import status


def test_login_success(get_client_connection):
    client, _ = get_client_connection

    payload = {
        "username": "test user",
        "email": "test_user@gmail.com",
        "password": "password",
    }

    response = client.post("/users", json=payload)

    assert response.status_code == status.HTTP_201_CREATED

    payload = {"email": "test_user@gmail.com", "password": "password"}

    response = client.post("/auth", json=payload)

    assert response.status_code == status.HTTP_200_OK
    body = response.json()

    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_failed_login_due_to_wrong_email(get_client_connection):
    client, _ = get_client_connection

    payload = {
        "username": "test user",
        "email": "test_user@gmail.com",
        "password": "password",
    }

    response = client.post("/users", json=payload)

    assert response.status_code == status.HTTP_201_CREATED

    payload = {"email": "testuser@gmail.com", "password": "password"}

    response = client.post("/auth", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body["detail"] == "invalid user credentials"


def test_failed_login_due_to_wrong_password(get_client_connection):
    client, _ = get_client_connection

    payload = {
        "username": "test user",
        "email": "test_user@gmail.com",
        "password": "password",
    }

    response = client.post("/users", json=payload)

    assert response.status_code == status.HTTP_201_CREATED

    payload = {"email": "test_user@gmail.com", "password": "passwor"}

    response = client.post("/auth", json=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body["detail"] == "invalid user credentials"
