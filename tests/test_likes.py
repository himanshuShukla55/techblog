from fastapi import status
from sqlmodel import Session, func, select

from techblog.models.likes import Like


def test_post_like_success(get_client_connection, like_blog_factory):
    _, connection = get_client_connection
    blog_id, like = like_blog_factory
    assert "user_id" in like
    assert like["blog_id"] == blog_id
    assert "created_at" in like

    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        db_like = session.exec(
            select(Like).where(Like.blog_id == blog_id)
        ).one_or_none()
        assert db_like is not None


def test_failed_post_like_if_user_has_already_liked_the_blog(
    get_client_connection, auth_factory, like_blog_factory
):
    client, connection = get_client_connection
    authenticate_user = auth_factory
    _, auth_headers = authenticate_user()
    blog_id, _ = like_blog_factory

    res = client.post(f"/blogs/{blog_id}/like", headers=auth_headers)

    assert res.status_code == status.HTTP_409_CONFLICT
    assert res.json()["detail"] == "user cannot like the same blog twice!"

    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        count = session.exec(
            select(func.count()).select_from(Like).where(Like.blog_id == blog_id)
        ).one()
        assert count == 1


def test_failed_like_blog_because_blog_not_found(get_client_connection, auth_factory):
    client, _ = get_client_connection
    authenticate_user = auth_factory
    _, auth_header = authenticate_user()

    res = client.post(
        "/blogs/75d64418-ee42-4aa9-a5fb-04ab04252f4b/like", headers=auth_header
    )

    assert res.status_code == status.HTTP_404_NOT_FOUND
    assert res.json()["detail"] == "blog not found!"


def test_success_unlike_blog(get_client_connection, like_blog_factory, auth_factory):
    client, connection = get_client_connection
    blog_id, _ = like_blog_factory
    authenticate_user = auth_factory
    user_id, auth_header = authenticate_user()

    res = client.delete(f"/blogs/{blog_id}/like", headers=auth_header)

    assert res.status_code == status.HTTP_204_NO_CONTENT

    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        like = session.exec(
            select(Like).where(Like.user_id == user_id, Like.blog_id == blog_id)
        ).one_or_none()
        assert like is None


def test_failed_unlike_because_token_is_missing(
    get_client_connection, like_blog_factory
):
    client, connection = get_client_connection
    blog_id, like = like_blog_factory

    res = client.delete(f"/blogs/{blog_id}/like")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        db_like = session.exec(
            select(Like).where(
                Like.user_id == like["user_id"], Like.blog_id == like["blog_id"]
            )
        ).one_or_none()
        assert db_like is not None


def test_failed_unlike_because_unauhthorized_user(
    get_client_connection, register_user_factory, auth_factory, like_blog_factory
):
    client, connection = get_client_connection
    blog_id, like = like_blog_factory
    authenticate_user = auth_factory
    register_user = register_user_factory

    user = register_user("test_user_2", "test2@gmail.com", "Password@2")
    _, auth_header = authenticate_user(user)

    res = client.delete(f"/blogs/{blog_id}/like", headers=auth_header)
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert res.json()["detail"] == "Unauthorized!"

    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        db_like = session.exec(
            select(Like).where(
                Like.user_id == like["user_id"], Like.blog_id == like["blog_id"]
            )
        ).one_or_none()
        assert db_like is not None
