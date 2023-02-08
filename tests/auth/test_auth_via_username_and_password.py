from http import HTTPStatus

import pytest

from app.api.auth.types import AccessTokenType

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "data",
    (
        ({"username": "aasd"}),
        ({"password": "asdasdas"}),
        ({"some_field": "value"}),
    ),
)
async def test_invalid_request_data(async_client, data):
    response = await async_client.post("/auth/token", data=data)
    assert response.status_code == HTTPStatus.BAD_REQUEST, response.text


async def test_cant_auth_user_not_in_db(async_client):
    some_random_username = "asdaksslgkafdglkafhbg"
    data = {"username": some_random_username, "password": "asdasd"}

    response = await async_client.post("/auth/token", data=data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_cant_auth_user_with_wrong_password(async_client):
    # create user in db
    username = "appleapple"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": username,
        "password": "wylsawylsa",
        "email": "sj@apple.com",
    }
    await async_client.post("/users", json=user_data)

    # trying to auth with wrong password
    auth_data = {"username": username, "password": "randomrandom"}
    response = await async_client.post("/auth/token", data=auth_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_success_auth(async_client):
    # create user in db
    username, password = "stevesteve", "appleapple"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": username,
        "password": password,
        "email": "sj@apple.com",
    }
    await async_client.post("/users", json=user_data)

    auth_data = {"username": username, "password": password}
    response = await async_client.post("/auth/token", data=auth_data)
    assert response.status_code == HTTPStatus.OK, response.text

    json_response = response.json()

    assert "access_token" in json_response, json_response
    assert "token_type" in json_response, json_response

    assert len(json_response["access_token"]) != 0, json_response
    assert json_response["token_type"] == AccessTokenType.BEARER, json_response
