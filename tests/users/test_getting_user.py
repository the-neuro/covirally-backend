import uuid
from http import HTTPStatus

import pytest
from jose import jwt

from app.api.auth.password_utils import passwords_are_equal, get_password_hash
from app.api.auth.utils import create_access_token, ALGORITHM
from app.config import settings
from app.db.models.users.handlers import create_user
from app.schemas import CreateUser

pytestmark = pytest.mark.asyncio


async def test_success_get(async_client):
    password, email = "appleapple", "svsj@apple.com"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "ddmvaa2d",
        "password": get_password_hash(password),
        "email": email,
        "email_is_verified": True,
    }
    await create_user(CreateUser.construct(**user_data))

    auth_data = {"email": email, "password": password}
    auth_response = await async_client.post("/auth/token", data=auth_data)

    auth_response_json = auth_response.json()

    assert "access_token" in auth_response_json, auth_response_json

    access_token = auth_response_json["access_token"]
    auth_header = f"Bearer {access_token}"

    response = await async_client.get("/users/me", headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.OK

    user_response = response.json()

    assert "id" in user_response, user_response
    assert "created_at" in user_response, user_response
    assert user_response["first_name"] == user_data["first_name"], user_response
    assert user_response["last_name"] == user_data["last_name"], user_response
    assert user_response["username"] == user_data["username"], user_response
    assert user_response["email"] == user_data["email"], user_response

    assert passwords_are_equal(
        password=password, hashed_password=user_response["password"]
    ), "password didn't match"


async def test_get_while_unauthorized(async_client):
    response = await async_client.get("/users/me")
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_get_with_wrong_email_payload(async_client):
    # create access token with wrong email
    access_token = create_access_token(email="hello@gmail.com")
    auth_header = f"Bearer {access_token}"

    response = await async_client.get("/users/me", headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_get_with_wrong_params_in_payload(async_client):
    # leave payload empty
    token: str = jwt.encode({}, settings.secret_jwt_token, algorithm=ALGORITHM)

    auth_header = f"Bearer {token}"

    response = await async_client.get("/users/me", headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_with_random_access_token(async_client):
    auth_header = f"Bearer {uuid.uuid4()}"

    response = await async_client.get("/users/me", headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_get_with_outdated_token(async_client):
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "stevesteve",
        "password": get_password_hash("password"),
        "email": "sj@apple.com",
        "email_is_verified": True,
    }
    await create_user(CreateUser.construct(**user_data))

    # create outdated token
    access_token = create_access_token(email=user_data["email"], expires_minutes=-123)

    auth_header = f"Bearer {access_token}"
    response = await async_client.get("/users/me", headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text
