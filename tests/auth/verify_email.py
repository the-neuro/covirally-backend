from http import HTTPStatus

import pytest

from app.api.auth.password_utils import get_password_hash
from app.api.auth.verify_email import create_verify_email_token
from app.db.models.users.handlers import create_user, get_user
from app.schemas import CreateUser, GetUser
from tests.utils import get_random_string

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
async def user(async_client) -> GetUser:
    """
    Create not verified user
    """
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "appleapple",
        "password": get_password_hash("slsdakvn"),
        "email": "sjvasvmds@apple.com",
        "email_is_verified": False,
    }
    user, _ = await create_user(CreateUser.construct(**user_data))
    return user


async def test_success_verify_email(async_client, user: GetUser):
    # email is not verified
    assert not user.email_is_verified

    token = create_verify_email_token(email=user.email)
    response = await async_client.get(f"/auth/verifyemail/{token}", allow_redirects=False)
    assert response.status_code == HTTPStatus.PERMANENT_REDIRECT, response.text

    # email is verified
    user_in_db = await get_user(user_id=user.id)
    assert user_in_db.email_is_verified, f"Email {user.email} is not verified"
    assert user_in_db.email_verified_at is not None


@pytest.mark.parametrize(
    "invalid_token",
    (
        "asd",
        get_random_string(64),
    ),
)
async def test_wrong_verify_email_token(async_client, invalid_token, user: GetUser):
    response = await async_client.get(f"/auth/verifyemail/{invalid_token}")
    assert response.status_code == 400, response.text


async def test_doesnt_exist_email_in_verify_email_token(async_client):
    token = create_verify_email_token(email="doesntexist@gmail.com")
    response = await async_client.get(f"/auth/verifyemail/{token}")
    assert response.status_code == 404, response.text
