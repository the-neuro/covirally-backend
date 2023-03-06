import json
import uuid
from http import HTTPStatus

import pytest
from jose import jwt
from sqlalchemy import select, func

from app.api.auth.password_utils import passwords_are_equal, get_password_hash
from app.api.auth.utils import create_access_token, ALGORITHM
from app.config import settings
from app.db.base import database
from app.db.models.users.handlers import get_user_by_email, create_user
from app.db.models.users.schemas import User
from app.schemas import GetUser, CreateUser

pytestmark = pytest.mark.asyncio

PASSWORD = "stevesteve"


@pytest.fixture(scope="module")
async def access_token_and_user(async_client) -> tuple[str, GetUser]:
    """
    Create user, authorize it and get access token with username
    """
    email = "sjvas@apple.com"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "appleapple",
        "password": get_password_hash(PASSWORD),
        "email": email,
        "email_is_verified": True,
    }
    user, _ = await create_user(CreateUser.construct(**user_data))

    auth_data = {"email": email, "password": PASSWORD}
    auth_response = await async_client.post("/auth/token", data=auth_data)

    access_token = auth_response.json()["access_token"]
    return access_token, user


@pytest.mark.parametrize(
    "patch_data",
    (
        ({"first_name": "SomeName"}),
        ({"last_name": "LastName"}),
        ({"username": "new_one"}),
        ({"avatar_url": "https://asdasd.com"}),
        ({"receive_email_alerts": False}),
        ({"first_name": "Gello", "last_name": "ASdsd", "avatar_url": None})
    ),
)
async def test_success_patch_simple_fields(async_client, patch_data, access_token_and_user):
    access_token, user = access_token_and_user
    auth_header = f"Bearer {access_token}"

    patch_response = await async_client.patch("/users", json=patch_data, headers={"Authorization": auth_header})
    assert patch_response.status_code == HTTPStatus.OK, patch_response.text

    # returned edited fields
    patch_response_json = patch_response.json()
    assert patch_response_json == patch_data

    user_id_db = await get_user_by_email(user.email)
    assert user_id_db is not None

    # asswert value in db equal to value from request
    for field_name, value in patch_data.items():
        assert getattr(user_id_db, field_name) == value


async def test_success_change_password(async_client, access_token_and_user):
    access_token, user = access_token_and_user
    auth_header = f"Bearer {access_token}"

    tmp_password = "hello, password"
    patch_data = {
        "old_password": PASSWORD, "password": tmp_password
    }
    patch_response = await async_client.patch("/users", json=patch_data, headers={"Authorization": auth_header})
    patch_response_json = patch_response.json()

    # password changed and new one in response
    user_in_db = await get_user_by_email(user.email)
    assert passwords_are_equal(patch_data["password"], patch_response_json.get("password")), patch_response_json
    assert passwords_are_equal(patch_data["password"], user_in_db.password)

    # change password to initial one
    patch_data = {
        "old_password": tmp_password, "password": PASSWORD
    }
    patch_response = await async_client.patch("/users", json=patch_data, headers={"Authorization": auth_header})
    patch_response_json = patch_response.json()

    # password changed and new one in response
    user_in_db = await get_user_by_email(user.email)
    assert passwords_are_equal(patch_data["password"], patch_response_json.get("password")), patch_response_json
    assert passwords_are_equal(patch_data["password"], user_in_db.password)


@pytest.mark.parametrize(
    "patch_data",
    (
        ({"password": "some_password"}),  # old password is required
        ({"old_password": PASSWORD}),  # new password is required
        ({"old_password": PASSWORD, "password": PASSWORD}),  # equal passwords
        ({"old_password": str(uuid.uuid4()), "password": "password"}),  # wrong old password  # noqa
    )
)
async def test_bad_password_requests(async_client, patch_data, access_token_and_user):
    access_token, user = access_token_and_user
    auth_header = f"Bearer {access_token}"

    patch_response = await async_client.patch("/users", json=patch_data,
                                              headers={"Authorization": auth_header})
    assert patch_response.status_code == HTTPStatus.BAD_REQUEST, patch_response.text

    user_in_db = await get_user_by_email(user.email)
    assert user_in_db is not None

    # password didn't changed
    assert passwords_are_equal(PASSWORD, hashed_password=user_in_db.password)


async def test_cant_update_to_existing_username(async_client, access_token_and_user):
    new_username = "new_username"
    another_user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": new_username,
        "password": PASSWORD,
        "email": "sj@apple.com",
    }
    await async_client.post("/users", json=another_user_data)

    patch_data = {"username": new_username}
    access_token, _ = access_token_and_user
    auth_header = f"Bearer {access_token}"

    # can't patch it
    patch_response = await async_client.patch("/users", json=patch_data,
                                              headers={"Authorization": auth_header})
    assert patch_response.status_code == HTTPStatus.BAD_REQUEST, patch_response.text

    # only one user in db with such username
    users_count_query = select(func.count()).select_from(User).where(
        User.username == new_username)
    users_count: int = await database.execute(users_count_query)
    assert users_count == 1, f"Only one user must be with {new_username=}"


async def test_cant_update_to_existing_email(async_client, access_token_and_user):
    new_email = "gjasoivn@gmail.com"
    another_user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "dbvansdlq",
        "password": PASSWORD,
        "email": new_email,
    }
    await async_client.post("/users", json=another_user_data)

    patch_data = {"email": new_email}
    access_token, _ = access_token_and_user
    auth_header = f"Bearer {access_token}"

    # can't patch it, already have user with this email
    patch_response = await async_client.patch("/users", json=patch_data,
                                              headers={"Authorization": auth_header})
    assert patch_response.status_code == HTTPStatus.BAD_REQUEST, patch_response.text

    # only one user in db with such email
    users_count_query = select(func.count()).select_from(User).where(
        User.email == new_email)
    users_count: int = await database.execute(users_count_query)
    assert users_count == 1, f"Only one user must be with {new_email=}"


@pytest.mark.parametrize(
    "patch_data",
    (
        ({"id": str(uuid.uuid4())}),
        ({"created_at": "2023-02-07T09:46:37.905192"}),
    ),
)
async def test_cant_patch_system_fields(async_client, patch_data, access_token_and_user):
    access_token, user = access_token_and_user
    auth_header = f"Bearer {access_token}"

    patch_response = await async_client.patch("/users", json=patch_data,
                                              headers={"Authorization": auth_header})
    assert patch_response.status_code == HTTPStatus.BAD_REQUEST, patch_response.text

    user_id_db = await get_user_by_email(user.email)
    assert user_id_db is not None

    # asswert value in db doesn't equal to value from request
    for field_name, value in patch_data.items():
        assert getattr(user_id_db, field_name) != value


@pytest.mark.parametrize(
    "patch_data",
    (
        ({"first_name": ""}),
        ({"first_name": None}),
        ({"first_name": "jdnfhvygfuewhjbfkwjnwros9xuncbufsygvhilscfjbjgoesdnbsverkguehcvwnhieuvbsyyk"}),
        ({"last_name": ""}),
        ({"last_name": None}),
        ({"last_name": "jdnfhvygfuewhjbfkwjnwros9xuncbufsygvhilscfjbjgoesdnbsverkguehcvwnhieuvbsyyk"}),
        ({"email": "asdasd@gmailcom"}),
        ({"email": "@gmailcom"}),
        ({"email": "asdasdgmailcom"}),
        ({"email": "asdasd@gmail."}),
        ({"email": "asksdjnasjkdansdkdajskdnsd@gmail.com"}),  # too long email
        ({"avatar_url": "https:/google.com"}),
        ({"avatar_url": "https:google.com"}),
        ({"avatar_url": "https//google.com"}),
        ({"username": "a"}),  # too short username
    ),
)
async def test_wrong_data_format(async_client, patch_data, access_token_and_user):
    access_token, user = access_token_and_user
    auth_header = f"Bearer {access_token}"

    patch_response = await async_client.patch("/users", json=patch_data,
                                              headers={"Authorization": auth_header})
    assert patch_response.status_code == HTTPStatus.BAD_REQUEST, patch_response.text

    user_id_db = await get_user_by_email(user.email)
    assert user_id_db is not None

    # asswert value in db doesn't equal to value from request
    for field_name, value in patch_data.items():
        assert getattr(user_id_db, field_name) != value


async def test_patch_while_unauthorized(async_client):
    response = await async_client.patch("/users")
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_patch_with_wrong_email_payload(async_client):
    # create access token with wrong email
    access_token = create_access_token(email="ld@gmail.com")
    auth_header = f"Bearer {access_token}"

    response = await async_client.patch("/users", headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_patch_with_wrong_params_in_payload(async_client):
    # leave payload empty
    token: str = jwt.encode({}, settings.secret_jwt_token, algorithm=ALGORITHM)

    auth_header = f"Bearer {token}"

    response = await async_client.patch("/users", headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_with_random_access_token(async_client):
    auth_header = f"Bearer {uuid.uuid4()}"

    response = await async_client.patch("/users", headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_patch_with_outdated_token(async_client):
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "stevesteveasd",
        "email": "sjvvswwpj@apple.com",
        "password": get_password_hash("appleapple"),
        "email_is_verified": True,
    }
    await create_user(CreateUser.construct(**user_data))
    # create outdated token
    access_token = create_access_token(email=user_data["email"], expires_minutes=-123)

    auth_header = f"Bearer {access_token}"
    response = await async_client.patch("/users", headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text
