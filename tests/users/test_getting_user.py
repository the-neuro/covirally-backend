import json
import uuid
from http import HTTPStatus

import pytest
from jose import jwt

from app.api.auth.password_utils import passwords_are_equal
from app.api.auth.utils import create_access_token, ALGORITHM
from app.config import settings

pytestmark = pytest.mark.asyncio


async def test_success_get(async_client):
    username, password = "stevesteveasd", "appleapple"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": username,
        "password": password,
        "email": "sj@apple.com",
    }
    await async_client.post("/users", json=user_data)

    auth_data = {"username": username, "password": password}
    auth_response = await async_client.post("/auth/token", data=auth_data)

    access_token = auth_response.json()["access_token"]
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
        password=user_data["password"], hashed_password=user_response["password"]
    ), "password didn't match"


async def test_get_while_unauthorized(async_client):
    response = await async_client.get("/users/me")
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_get_with_wrong_used_id_payload(async_client):
    # create access token with wrong user_id
    access_token = create_access_token(user_id=str(uuid.uuid4()))
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
        "password": "appleapple",
        "email": "sj@apple.com",
    }
    response = await async_client.post("/users", json=user_data)
    response_json = json.loads(response.json())

    # create outdated token
    access_token = create_access_token(user_id=response_json["id"], expires_minutes=-123)

    auth_header = f"Bearer {access_token}"
    response = await async_client.get("/users/me", headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text
