import json
from datetime import datetime, timedelta, timezone

import pytest

from app.db.models.tasks.handlers import get_task_by_id
from app.schemas import GetUser
from app.types import TaskStatus
from tests.utils import get_iso_datetime_until_now, get_random_string

pytestmark = pytest.mark.asyncio
PASSWORD = "stevesteve"


@pytest.fixture(scope="module")
async def access_token_and_creator(async_client) -> tuple[str, GetUser]:
    """
    Create creator, authorize it and get access token with username
    """
    email = "sjvas@apple.com"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "appleapple",
        "password": PASSWORD,
        "email": email,
    }
    user_response = await async_client.post("/users", json=user_data)
    creator: GetUser = GetUser.construct(**json.loads(user_response.json()))

    auth_data = {"email": email, "password": PASSWORD}
    auth_response = await async_client.post("/auth/token", data=auth_data)

    access_token = auth_response.json()["access_token"]
    return access_token, creator


@pytest.fixture(scope="module")
async def access_token_and_user(async_client) -> tuple[str, GetUser]:
    """
    Create user, authorize it and get access token with username
    """
    email = "sjvasalsdk@apple.com"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "subscriber",
        "password": PASSWORD,
        "email": email,
    }
    user_response = await async_client.post("/users", json=user_data)
    creator: GetUser = GetUser.construct(**json.loads(user_response.json()))

    auth_data = {"email": email, "password": PASSWORD}
    auth_response = await async_client.post("/auth/token", data=auth_data)

    access_token = auth_response.json()["access_token"]
    return access_token, creator


@pytest.mark.parametrize(
    "valid_data",
    (
        ({
            "title": "Hello",
            "description": "Something",
            "due_to_date": get_iso_datetime_until_now(days=1),
        }),
        ({
            "title": "Hello2",
            "description": "Something2",
            "due_to_date": get_iso_datetime_until_now(days=10),
            "status": TaskStatus.IN_PROGRESS,
        }),
    ),
)
async def test_valid_cases_create_task_by_user(
    async_client,
    valid_data,
        access_token_and_creator,
        access_token_and_user
):
    _, creator = access_token_and_creator
    access_token, user = access_token_and_user
    auth_header = f"Bearer {access_token}"
    valid_data['creator_id'] = creator.id
    valid_data['suggested_by_id'] = user.id

    response = await async_client.post("/tasks", json=valid_data, headers={"Authorization": auth_header})
    assert response.status_code == 201, response.text

    json_response = response.json()

    # authogenerated fields are in response
    assert "id" in json_response
    assert "created_at" in json_response

    # foreign key fields with full info are not in response
    assert "creator" not in json_response
    assert "suggested_by" not in json_response

    task_id = json_response["id"]
    task_in_db = await get_task_by_id(task_id)
    assert task_in_db is not None, f"Task {task_id} is not in db after POST /tasks"

    assert task_in_db.title == valid_data["title"]
    assert task_in_db.description == valid_data["description"]
    assert task_in_db.creator_id == valid_data["creator_id"]
    assert task_in_db.suggested_by_id == valid_data["suggested_by_id"]


@pytest.mark.parametrize(
    "valid_data",
    (
        ({
            "title": "Hello",
            "description": "Something",
            "due_to_date": get_iso_datetime_until_now(days=1),
        }),
        ({
            "title": "Hello2",
            "description": "Something2",
            "due_to_date": get_iso_datetime_until_now(days=10),
            "status": TaskStatus.IN_PROGRESS,
        }),
    ),
)
async def test_valid_cases_creating_task_by_creator(async_client, valid_data,
                                                    access_token_and_creator):
    access_token, creator = access_token_and_creator
    auth_header = f"Bearer {access_token}"
    valid_data['creator_id'] = creator.id

    response = await async_client.post("/tasks", json=valid_data, headers={"Authorization": auth_header})
    assert response.status_code == 201, response.text

    json_response = response.json()

    # authogenerated fields are in response
    assert "id" in json_response
    assert "created_at" in json_response

    # foreign key fields with full info are not in response
    assert "creator" not in json_response
    assert "suggested_by" not in json_response

    task_id = json_response["id"]
    task_in_db = await get_task_by_id(task_id)
    assert task_in_db is not None, f"Task {task_id} is not in db after POST /tasks"

    assert task_in_db.title == valid_data["title"]
    assert task_in_db.description == valid_data["description"]
    assert task_in_db.creator_id == valid_data["creator_id"]
    assert task_in_db.suggested_by_id == valid_data.get("suggested_by_id")


@pytest.mark.parametrize(
    "invalid_due_date",
    (
            get_iso_datetime_until_now(days=0, seconds=-1),
            get_iso_datetime_until_now(days=-1),
            get_iso_datetime_until_now(seconds=-1),
            get_iso_datetime_until_now(days=-10),
            get_iso_datetime_until_now(days=-10),
        "asdasd",
        "2020-01-01",
        "01-01-2020",
        ""
    ),
)
async def test_cant_create_task_with_invalid_due_date(
    async_client,
    invalid_due_date,
    access_token_and_creator,
):
    access_token, creator = access_token_and_creator
    auth_header = f"Bearer {access_token}"
    data = {
        "title": "title",
        "due_to_date": invalid_due_date,
        "creator_id": creator.id,
    }
    response = await async_client.post("/tasks", json=data, headers={"Authorization": auth_header})

    assert response.status_code == 400, response.text


@pytest.mark.parametrize(
    "invalid_title",
    (
        "",  # too short
        "2",  # too short
        get_random_string(130),  # too long
    ),
)
async def test_cant_create_task_with_invalid_title(
    async_client,
    invalid_title,
    access_token_and_creator,
):
    access_token, creator = access_token_and_creator
    auth_header = f"Bearer {access_token}"
    data = {
        "title": invalid_title,
        "creator_id": creator.id,
    }
    response = await async_client.post("/tasks", json=data, headers={"Authorization": auth_header})

    assert response.status_code == 400, response.text


@pytest.mark.parametrize(
    "valid_data",
    (
        ({
            "title": "Hello",
            "description": "Something",
            "due_to_date": get_iso_datetime_until_now(days=1),
        }),
    ),
)
async def test_assigned_at_is_set(
        async_client, valid_data, access_token_and_creator, access_token_and_user):
    access_token, creator = access_token_and_creator
    _, assignee = access_token_and_user
    auth_header = f"Bearer {access_token}"
    valid_data['creator_id'] = creator.id
    valid_data['assignee_id'] = assignee.id

    response = await async_client.post("/tasks", json=valid_data, headers={"Authorization": auth_header})
    assert response.status_code == 201, response.text

    json_response = response.json()

    task_id = json_response["id"]
    task_in_db = await get_task_by_id(task_id=task_id)
    assert task_in_db is not None, f"Task {task_id} is not in db after POST /tasks"

    assert task_in_db.title == valid_data["title"]
    assert task_in_db.description == valid_data["description"]
    assert task_in_db.creator_id == valid_data["creator_id"]
    assert task_in_db.assignee_id == valid_data["assignee_id"]

    assert task_in_db.assigned_at is not None, "assigned_at must be set when assignee_id is in POST /tasks"

    # check that assigned_at was set
    two_seconds_before = datetime.now(timezone.utc) - timedelta(seconds=2)
    two_seconds_after = datetime.now(timezone.utc) + timedelta(seconds=2)
    assert two_seconds_before < task_in_db.assigned_at
    assert task_in_db.assigned_at < two_seconds_after