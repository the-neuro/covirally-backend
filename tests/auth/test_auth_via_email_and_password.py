from http import HTTPStatus

import pytest

from app.api.auth.password_utils import get_password_hash
from app.api.auth.types import AccessTokenType
from app.db.models.users.handlers import create_user
from app.schemas import CreateUser

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "data, status_code",
    (
        ({"username": "aasd"}, HTTPStatus.BAD_REQUEST),
        ({"password": "asdasdas"}, HTTPStatus.BAD_REQUEST),
        ({"some_field": "value"}, HTTPStatus.BAD_REQUEST),
        ({"username": "asd"}, HTTPStatus.BAD_REQUEST),
        ({"username": "ga@gmail.com"}, HTTPStatus.BAD_REQUEST),
        ({"username": "gagmail.com", "password": "adasd"}, HTTPStatus.NOT_FOUND),
        ({"username": "dasd", "password": "asdasdas"}, HTTPStatus.NOT_FOUND),
    ),
)
async def test_invalid_request_data(async_client, data, status_code):
    response = await async_client.post("/auth/token", data=data)
    assert response.status_code == status_code, response.text


async def test_cant_auth_user_not_in_db(async_client):
    some_random_email = "asd@gmail.com"
    data = {"username": some_random_email, "password": "asdasd"}

    response = await async_client.post("/auth/token", data=data)
    assert response.status_code == HTTPStatus.NOT_FOUND, response.text


async def test_cant_auth_user_with_wrong_password(async_client):
    # create user in db
    username, email = "appleapple", "sj@apple.com"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": username,
        "password": "wylsawylsa",
        "email": email,
    }
    await async_client.post("/users", json=user_data)

    # trying to auth with wrong password
    auth_data = {"username": email, "password": "randomrandom"}
    response = await async_client.post("/auth/token", data=auth_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_cant_auth_with_not_verified_email(async_client):
    email, password = "sjbdfvdf@apple.com", "dfslbnsrn"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "appleapplalskde",
        "password": get_password_hash(password),
        "email": email,
        "email_is_verified": False,
    }
    await create_user(CreateUser.construct(**user_data))

    auth_data = {"username": email, "password": password}
    response = await async_client.post("/auth/token", data=auth_data)
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_success_auth(async_client):
    # create user in db
    username, password, email = "stevesteve", "appleapple", "sjvvxcvxcv@apple.com"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": username,
        "password": get_password_hash(password),
        "email": email,
        "email_is_verified": True,
    }
    await create_user(CreateUser.construct(**user_data))

    auth_data = {"username": email, "password": password}
    response = await async_client.post("/auth/token", data=auth_data)
    assert response.status_code == HTTPStatus.OK, response.text

    json_response = response.json()

    assert "access_token" in json_response, json_response
    assert "token_type" in json_response, json_response

    assert len(json_response["access_token"]) != 0, json_response
    assert json_response["token_type"] == AccessTokenType.BEARER, json_response
