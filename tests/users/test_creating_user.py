import uuid
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import select, func

from app.api.auth.password_utils import passwords_are_equal
from app.db.base import database
from app.db.models.users.handlers import get_user_by_email
from app.db.models.users.schemas import User
from tests.utils import get_iso_datetime_until_now

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "valid_data",
    (
        ({
            "first_name": "Steve",
            "last_name": "Jobs",
            "username": "steve_jobs",
            "password": "appleapple",
            "email": "sjpd@apple.com",
            "receive_email_alerts": True,
            "avatar_url": "https://google.com/some_picture.jpg",
        }),
        ({
            "first_name": "SteveSteveSteve",
            "last_name": "JobsJobsJobs",
            "username": "steve_jobs_Asd",
            "password": "appleapple",
            "email": "sjca@apple.com",
            "avatar_url": "https://google.com/some_picture.jpg",
        }),
        ({
            "first_name": "SteveSteveSteve",
            "last_name": "SteveSteveSteve",
            "username": "steve_jobs_dasd_31",
            "password": "appleapple",
            "email": "sjkon@apple.com",
            "receive_email_alerts": True,
            "avatar_url": "https://google.com/some_picture.jpg",
        }),
        ({
            "first_name": "Steve",
            "last_name": "Jobs",
            "username": "steve_jobs_asd",
            "password": "appleapple",
            "email": "sj2@apple.com",
            "receive_email_alerts": True,
        }),
        ({
            "first_name": "Steve",
            "last_name": "Jobs",
            "username": "steve_jobs_331",
            "password": "appleapple",
            "email": "sjxv@apple.com",
        }),
        ({
            "first_name": "Steve",
            "last_name": "Jobs",
            "username": "steve_jobs_33amsldk1",
            "password": "appleapple",
            "email": "sjlasddajlskdjlnalsdj4215@apple.com",
        }),
        ({
            "password": "appleapple",
            "email": "sjxv@appcakle.com",
        }),
        ({
            "last_name": "Jobs",
            "username": "steve_jobs_331v2",
            "password": "appleapple",
            "email": "sjxv@apkfople.com",
        }),
        ({
            "first_name": "Steve",
            "username": "steve_jobs_331va",
            "password": "appleapple",
            "email": "sjxv@vsdapple.com",
        }),
        ({
            "username": "steve_jobs_asdm31",
            "password": "appleapple",
            "email": "sjxv@applbowne.com",
        }),
    ),
)
@patch("app.api.users.routers.create_verify_token_and_send_to_email", return_value=None)
async def test_valid_cases(send_verification_email: MagicMock, async_client, valid_data):
    """
    Test all valid cases for creating users
    Assert that required fields are in response
    """
    response = await async_client.post("/users", json=valid_data)

    assert response.status_code == 201, response.text

    user_in_db = await get_user_by_email(valid_data["email"])
    assert user_in_db is not None

    assert user_in_db.first_name == valid_data.get("first_name")
    assert user_in_db.last_name == valid_data.get("last_name")
    assert user_in_db.email == valid_data["email"]
    assert user_in_db.username == valid_data.get("username")
    assert user_in_db.receive_email_alerts == valid_data.get("receive_email_alerts", True)
    assert user_in_db.avatar_url == valid_data.get("avatar_url")
    assert not user_in_db.email_is_verified
    assert user_in_db.email_verified_at is None

    # check that password is hashed and equal to one from request
    assert passwords_are_equal(
        password=valid_data["password"], hashed_password=user_in_db.password
    )

    # check that confirmation email is sent
    send_verification_email.assert_called_once_with(email=valid_data['email'])

    json_response = response.json()
    for key in ("id", "created_at"):
        assert key in json_response


async def test_cant_create_with_same_usernames(async_client):
    data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "steve_jobs_asdasdvxc",
        "password": "appleapple",
        "email": "sj@applcaqwe.com",
    }

    # creating 1'st time, check that everything is ok
    response = await async_client.post("/users", json=data)
    assert response.status_code == 201, response.text

    # creating 2nd time, must be bad request
    response = await async_client.post("/users", json=data)
    err = "Must be 400 because trying to create with same usernmae"
    assert response.status_code == 400, err

    # ensure that only 1 user in db
    users_count_query = select(func.count()).select_from(User).where(
        User.username == data["username"])
    users_count: int = await database.execute(users_count_query)
    assert users_count == 1, f"Must be only one user with username={data['username']}"


async def test_cant_create_with_same_emails(async_client):
    data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "steve_jobs_asdasdvx",
        "password": "appleapple",
        "email": "sj132asdmv@apple.com",
    }

    # creating 1'st time, check that everything is ok
    response = await async_client.post("/users", json=data)
    assert response.status_code == 201, response.text

    # creating 2nd time, must be bad request
    data["username"] = None
    response = await async_client.post("/users", json=data)
    err = "Must be 400 because trying to create with same email"
    assert response.status_code == 400, err

    # ensure that only 1 user in db
    users_count_query = select(func.count()).select_from(User).where(
        User.email == data["email"])
    users_count: int = await database.execute(users_count_query)
    assert users_count == 1, f"Must be only one user with email={data['email']}"


@pytest.mark.parametrize(
    "data",
    (
        ({"first_name": "aasd"}),
        ({"first_name": "aasd", "last_name": "asd"}),
        ({"first_name": "aasd", "last_name": "asd", "username": "addsasd", "email": "asd@gmail.com"}),
        ({"first_name": "aasd", "last_name": "asd", "username": "addsasd", "password": "asdasdasd", "email": "asaskdjnasldkjnasdlkajsdna@gmail.com"}),
        ({"first_name": "aasd", "last_name": "asd", "username": "addsasd", "password": "1", "email": "asd@gmail.com"}),
        ({"first_name": "aasd", "last_name": "asd", "username": "addsasd", "password": "1"}),
        ({"first_name": "aasd", "last_name": "asd", "username": "1", "password": "asdasdasd", "email": "asd@gmail.com"}),
    ),
)
async def test_invalid_cases(async_client, data):
    response = await async_client.post("/users", json=data)

    assert response.status_code == 400, response.text


@pytest.mark.parametrize(
    "system_fields",
    (
        ({"id": str(uuid.uuid4())}),
        ({"created_at": get_iso_datetime_until_now()}),
        ({"email_is_verified": True}),
        ({"email_is_verified": False}),
        ({"email_verified_at": get_iso_datetime_until_now(days=2)}),
        ({"email_verified_at": None}),
    ),
)
async def test_cant_create_with_system_fields(async_client, system_fields):
    email = "sjxkafdsjcv@apple.com"
    valid_user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "steve_joalfgbs_331",
        "password": "appleapple",
        "email": email,
    }
    user_data_with_system_fields = dict(**valid_user_data, **system_fields)

    response = await async_client.post("/users", json=user_data_with_system_fields)
    assert response.status_code == 400, f"Can't change system fields: {response.text}"

    user_in_db = await get_user_by_email(email)
    assert user_in_db is None, f"User cant be created with system fields: {system_fields}"
