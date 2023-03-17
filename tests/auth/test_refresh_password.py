from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest
from jose import jwt

from app.api.auth.password_utils import get_password_hash, passwords_are_equal
from app.api.auth.refresh_password import create_refresh_password_token, \
    REFRESH_PASSWORD_EXPIRES_HOURS
from app.api.auth.utils import ALGORITHM
from app.config import settings
from app.db.models.users.handlers import create_user, get_user, update_user
from app.schemas import CreateUser, GetUser
from tests.utils import get_random_string

pytestmark = pytest.mark.asyncio

PASSWORD = "appleapple"


@pytest.fixture(scope="module")
async def user() -> GetUser:
    username, email = "stevesteve", "sjvvxcvxcv@apple.com"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": username,
        "password": get_password_hash(PASSWORD),
        "email": email,
        "email_is_verified": True,
    }
    creator, _ = await create_user(CreateUser.construct(**user_data))
    return creator


@patch("app.api.auth.routers.create_refresh_password_token_and_send", return_value=None)
async def test_success_sent_refresh_password_email(
    create_and_send_refresh_token: MagicMock, async_client, user: GetUser
):
    email = user.email
    data = {'email': email}
    response = await async_client.post("/auth/refresh-password", json=data)
    assert response.status_code == 200, response.text

    # ensure that email is sent and called with appropriate email
    create_and_send_refresh_token.assert_called_once_with(
        email=email,
        avatar_url=user.avatar_url,
        username=user.username,
    )


async def test_success_change_password(async_client, user: GetUser):
    token = create_refresh_password_token(user.email)
    new_password = "nasdnasdvsd"
    data = {"password": new_password}

    response = await async_client.post(f"/auth/refresh-password/{token}", json=data)
    assert response.status_code == 200, response.text

    # password is changed
    user_in_db = await get_user(user_id=user.id)
    assert passwords_are_equal(
        password=new_password, hashed_password=user_in_db.password
    )

    # rollback to old password
    await update_user(user_id=user.id, values={"password": get_password_hash(PASSWORD)})


@pytest.mark.parametrize(
    "invalid_data",
    (
        ({"password": "gjasldk"}),  # too short
        ({"password": get_random_string(65)}),  # too long
    ),
)
async def test_wrong_data_for_changing_password(async_client, invalid_data, user: GetUser):
    refresh_token = create_refresh_password_token(user.email)
    response = await async_client.post(f"/auth/refresh-password/{refresh_token}", json=invalid_data)
    assert response.status_code == 400, response.text


async def test_change_password_for_non_existing_user(async_client):
    refresh_token = create_refresh_password_token("asgka@gmail.com")
    data = {"password": "newpassword"}
    response = await async_client.post(f"/auth/refresh-password/{refresh_token}", json=data)
    assert response.status_code == 400, response.text


async def test_change_password_with_expired_token(async_client, user: GetUser):
    refresh_token = create_refresh_password_token(user.email, expires_hours=-2)
    data = {"password": "newpassword"}
    response = await async_client.post(f"/auth/refresh-password/{refresh_token}", json=data)
    assert response.status_code == 400, response.text

    # password didn't change
    user_in_db = await get_user(user_id=user.id)
    assert passwords_are_equal(
        password=PASSWORD, hashed_password=user_in_db.password
    )



@pytest.mark.parametrize(
    "invalid_data",
    (
        ({"email": "aasd"}),
        ({"email": "asdgmail.com"}),
        ({"email": ""}),
        ({"email": "asdga@gmail"}),
        ({}),
        ({"email": "gaaslkgmaasdlasnkdsdlgangk@gmail.com"}),  # too long
    ),
)
async def test_wrong_data_format_for_sending_token(async_client, invalid_data):
    response = await async_client.post("/auth/refresh-password", json=invalid_data)
    assert response.status_code == 400, response.text


async def test_send_refresh_password_email_for_not_exist_user(async_client):
    data = {
        'email': 'somerandomemail@gmail.com'
    }

    response = await async_client.post("/auth/refresh-password", json=data)
    assert response.status_code == 404, response.text


async def test_refresh_password_token():
    email = "someemail@gmail.com"

    token = create_refresh_password_token(email=email)

    payload = jwt.decode(
        token, settings.secret_jwt_token, algorithms=[ALGORITHM]
    )

    # correct email in payload
    assert 'email' in payload, payload
    assert payload['email'] == email

    # token has expiration date
    assert 'exp' in payload, payload

    # expiration datetime is set properly
    token_exp = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
    possible_exp = datetime.now(tz=timezone.utc) + timedelta(hours=REFRESH_PASSWORD_EXPIRES_HOURS)
    assert possible_exp - timedelta(minutes=1) < token_exp < possible_exp + timedelta(minutes=1)
