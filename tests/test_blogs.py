from fastapi import status
from sqlmodel import Session, func, select

from techblog.models.blogs import Blog


def test_failed_post_blog_because_token_is_missing(get_client_connection):
    client, _ = get_client_connection

    res = client.post("/blogs", json={})
    body = res.json()
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert body["detail"] == "Not authenticated"


def test_success_post_blog(get_client_connection, blog_factory):
    _, connection = get_client_connection
    payload, blog = blog_factory

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


def test_failed_update_blog_due_to_wrong_token(
    get_client_connection, auth_factory, register_user_factory, blog_factory
):
    client, _ = get_client_connection
    register_user = register_user_factory
    authenticate_user = auth_factory

    _, blog = blog_factory

    user_two = register_user(
        username="test_user_2", email="test2@gmail.com", password="Password@2"
    )

    _, token_two = authenticate_user(user_two)
    payload = {"title": "Test Blog Updated", "body": "adfasdf"}

    res = client.patch(f"/blogs/{blog['id']}", json=payload, headers=token_two)

    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_failed_update_blog_because_blog_does_not_exist(
    get_client_connection, auth_factory
):
    client, _ = get_client_connection
    authenticate_user = auth_factory
    _, auth_header = authenticate_user()

    payload = {"title": "Changed Title"}
    res = client.patch(
        "/blogs/75d64418-ee42-4aa9-a5fb-04ab04252f4b",
        json=payload,
        headers=auth_header,
    )

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json()["detail"] == "blog not found!"


def test_success_update_blog(get_client_connection, auth_factory, blog_factory):
    client, _ = get_client_connection
    authenticate_user = auth_factory
    _, auth_header = authenticate_user()
    _, blog = blog_factory
    payload = {"title": "Updated Title"}
    res = client.patch(f"/blogs/{blog['id']}", json=payload, headers=auth_header)

    assert res.status_code == status.HTTP_200_OK

    updated_blog = res.json()

    assert blog["title"] != updated_blog["title"]
    assert updated_blog["title"] == payload["title"]


def test_delete_blog_success(get_client_connection, auth_factory, blog_factory):
    client, connection = get_client_connection
    authenticate_user = auth_factory
    _, auth_header = authenticate_user()
    _, blog = blog_factory

    res = client.delete(f"/blogs/{blog['id']}", headers=auth_header)

    assert res.status_code == status.HTTP_204_NO_CONTENT

    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        blog = session.get(Blog, blog["id"])
        assert blog is None


def test_failed_delete_blog_because_user_is_unauthorized(
    get_client_connection, register_user_factory, auth_factory, blog_factory
):
    client, connection = get_client_connection
    register_user = register_user_factory
    authenticate_user = auth_factory
    _, blog = blog_factory

    user = register_user("test_user_2", "test2@gmail.com", "Password@2")
    _, auth_header = authenticate_user(user)

    res = client.delete(f"/blogs/{blog['id']}", headers=auth_header)

    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.json()["detail"] == "user is forbidden to delete this blog"

    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        db_blog = session.get(Blog, blog["id"])
        assert db_blog is not None


def test_failed_delete_blog_because_blog_not_found(get_client_connection, auth_factory):
    client, _ = get_client_connection
    authenticate_user = auth_factory
    _, auth_header = authenticate_user()

    res = client.delete(
        "/blogs/75d64418-ee42-4aa9-a5fb-04ab04252f4b", headers=auth_header
    )

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json()["detail"] == "blog not found!"


def test_failed_delete_blog_missing_token(get_client_connection, blog_factory):
    client, connection = get_client_connection
    _, blog = blog_factory

    res = client.delete(f"/blogs/{blog['id']}")

    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json()["detail"] == "Not authenticated"

    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        db_blog = session.get(Blog, blog["id"])
        assert db_blog is not None
