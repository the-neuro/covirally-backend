import pytest
from sqlalchemy import select, func

from app.api.auth.password_utils import passwords_are_equal
from app.db.base import database
from app.db.models.users.handlers import get_user_by_username
from app.db.models.users.schemas import User


pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "valid_data",
    (
        ({
            "first_name": "Steve",
            "last_name": "Jobs",
            "username": "steve_jobs",
            "password": "appleapple",
            "email": "sj@apple.com",
            "receive_email_alerts": True,
            "telephone_number": "+71231231231",
            "avatar_url": "https://google.com/some_picture.jpg",
        }),
        ({
            "first_name": "SteveSteveSteve",
            "last_name": "JobsJobsJobs",
            "username": "steve_jobs_Asd",
            "password": "appleapple",
            "email": "sj@apple.com",
            "telephone_number": "+71231231231",
            "avatar_url": "https://google.com/some_picture.jpg",
        }),
        ({
            "first_name": "SteveSteveSteve",
            "last_name": "SteveSteveSteve",
            "username": "steve_jobs_dasd_31",
            "password": "appleapple",
            "email": "sj@apple.com",
            "receive_email_alerts": True,
            "avatar_url": "https://google.com/some_picture.jpg",
        }),
        ({
            "first_name": "Steve",
            "last_name": "Jobs",
            "username": "steve_jobs_asd",
            "password": "appleapple",
            "email": "sj@apple.com",
            "receive_email_alerts": True,
            "telephone_number": "+71231231231",
        }),
        ({
            "first_name": "Steve",
            "last_name": "Jobs",
            "username": "steve_jobs_331",
            "password": "appleapple",
            "email": "sj@apple.com",
        }),
    ),
)
async def test_valid_cases(async_client, valid_data):
    """
    Test all valid cases for creating users
    Assert that required fields are in response
    """
    response = await async_client.post("/users", json=valid_data)

    assert response.status_code == 201, response.text

    user_in_db = await get_user_by_username(valid_data["username"])
    assert user_in_db is not None

    assert user_in_db.first_name == valid_data["first_name"]
    assert user_in_db.last_name == valid_data["last_name"]
    assert user_in_db.username == valid_data["username"]
    assert user_in_db.email == valid_data["email"]
    assert user_in_db.receive_email_alerts == valid_data.get("receive_email_alerts", True)
    assert user_in_db.telephone_number == valid_data.get("telephone_number")
    assert user_in_db.avatar_url == valid_data.get("avatar_url")

    # check that password is hashed and equal to one from request
    assert passwords_are_equal(
        password=valid_data["password"], hashed_password=user_in_db.password
    )

    json_response = response.json()
    for key in ("id", "created_at"):
        assert key in json_response


async def test_cant_create_with_same_usernames(async_client):
    data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "steve_jobs_asdasd",
        "password": "appleapple",
        "email": "sj@apple.com",
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


@pytest.mark.parametrize(
    "data",
    (
        ({"first_name": "aasd"}),
        ({"first_name": "aasd", "last_name": "asd"}),
        ({"first_name": "aasd", "last_name": "asd", "username": "addsasd", "email": "asd@gmail.com"}),
        ({"first_name": "aasd", "last_name": "asd", "username": "addsasd", "password": "1", "email": "asd@gmail.com"}),
        ({"first_name": "aasd", "last_name": "asd", "username": "1asdsad", "password": "asdasdasd", "email": "asdgmail.com"}),
        ({"first_name": "aasd", "last_name": "asd", "username": "addsasd", "password": "1"}),
        ({"first_name": "aasd", "last_name": "asd", "username": "1", "password": "asdasdasd", "email": "asd@gmail.com"}),
    ),
)
async def test_invalid_cases(async_client, data):
    response = await async_client.post("/users", json=data)

    assert response.status_code == 400, response.text
