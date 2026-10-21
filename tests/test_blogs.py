from fastapi import status
from sqlmodel import Session, func, select

from techblog.models.blogs import Blog


def test_add_blog_without_token(test_client):
    client, _ = test_client

    res = client.post("/blogs", json={})
    body = res.json()
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert body["detail"] == "Not authenticated"


def test_success_post_blogs(test_client, test_auth):
    client, connection = test_client
    authenticate_user = test_auth

    payload = {"title": "Test Blog", "body": "This is the body of the Test Blog."}

    res = client.post("/blogs", json=payload, headers=authenticate_user())

    assert res.status_code == status.HTTP_201_CREATED
    blog = res.json()

    assert blog["title"] == payload["title"]
    assert blog["body"] == payload["body"]
    assert "created_at" in blog
    assert "id" in blog
    assert "author_id" in blog
    assert "updated_at" in blog

    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        count = session.exec(
            select(func.count()).select_from(Blog).where(Blog.title == payload["title"])
        ).one()
        assert count == 1


def test_failed_unauthorized_blog_update(test_client, test_auth, register_user_factory):
    client, _ = test_client
    register_user = register_user_factory
    authenticate_user = test_auth

    payload = {"title": "Test Blog", "body": "This is the body of the Test Blog."}

    res = client.post("/blogs", json=payload, headers=authenticate_user())

    assert res.status_code == status.HTTP_201_CREATED

    blog = res.json()

    user_two = register_user(
        username="test_user_2", email="test2@gmail.com", password="Password@2"
    )

    token_two = authenticate_user(user_two)
    payload = {"title": "Test Blog Updated", "body": "adfasdf"}

    res = client.patch(f"/blogs/{blog['id']}", json=payload, headers=token_two)

    assert res.status_code == status.HTTP_403_FORBIDDEN
