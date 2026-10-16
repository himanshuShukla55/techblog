from fastapi import status


def test_login_success(test_client):
    client, _ = test_client

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

    assert "user_id" in body
    assert body["message"] == "Login successful"


def test_wrong_email_failed_login(test_client):
    client, _ = test_client

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

def test_wrong_password_failed_login(test_client):
    client, _ = test_client

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
