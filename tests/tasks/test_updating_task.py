import json
import uuid
from datetime import datetime
from http import HTTPStatus

import pytest

from app.api.auth.password_utils import get_password_hash
from app.db.models.tasks.handlers import get_task_by_id
from app.db.models.users.handlers import create_user
from app.schemas import GetUser, GetTaskNoForeigns, CreateUser
from app.types import TaskStatus
from tests.utils import get_iso_datetime_until_now, get_random_string

PASSWORD = "asdkadfs"
pytestmark = pytest.mark.asyncio


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


@pytest.fixture(scope="module")
async def access_token_and_random_user(async_client) -> tuple[str, GetUser]:
    """
    Create random user, authorize it and get access token with username
    """
    email = "sjvafdlbvdfsas@apple.com"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "appleapplebnris",
        "password": get_password_hash(PASSWORD),
        "email": email,
        "email_is_verified": True,
    }
    user, _ = await create_user(CreateUser.construct(**user_data))

    auth_data = {"email": email, "password": PASSWORD}
    auth_response = await async_client.post("/auth/token", data=auth_data)

    access_token = auth_response.json()["access_token"]
    return access_token, user


@pytest.fixture(scope="module")
async def access_token_and_subscriber(async_client) -> tuple[str, GetUser]:
    """
    Create subscriber, authorize it and get access token with username
    """
    email = "sjvasdfsbklm@apple.com"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "asdkmaafvldf",
        "password": get_password_hash(PASSWORD),
        "email": email,
        "email_is_verified": True,
    }
    creator, _ = await create_user(CreateUser.construct(**user_data))

    auth_data = {"email": email, "password": PASSWORD}
    auth_response = await async_client.post("/auth/token", data=auth_data)

    access_token = auth_response.json()["access_token"]
    return access_token, creator


@pytest.fixture(scope="function")
async def created_task(async_client, access_token_and_user, access_token_and_subscriber) -> GetTaskNoForeigns:
    """Scope is function => new task is created per each test"""
    access_token, user = access_token_and_user
    _, subscriber = access_token_and_subscriber
    auth_header = f"Bearer {access_token}"

    data = {
        "title": "Hello",
        "Description": "Some description",
        "creator_id": user.id,
        "assignee_id": subscriber.id,
    }

    response = await async_client.post("/tasks", json=data, headers={"Authorization": auth_header})
    assert response.status_code == 201, response.text

    task = GetTaskNoForeigns.construct(**response.json())
    return task


@pytest.mark.parametrize(
    "patch_data",
    (
        ({"title": "Another title"}),
        ({"description": "Another description"}),
        ({"status": TaskStatus.IN_PROGRESS}),
        ({"status": TaskStatus.DONE}),
        ({"status": TaskStatus.IDEA, "title": "New title"}),
        ({"due_to_date": get_iso_datetime_until_now(days=1)}),
    ),
)
async def test_success_patch(
    patch_data,
    async_client,
    access_token_and_user: tuple[str, GetUser],
    created_task: GetTaskNoForeigns
):
    access_token, _ = access_token_and_user
    auth_header = f"Bearer {access_token}"

    response = await async_client.patch(f"/tasks/{created_task.id}", json=patch_data, headers={"Authorization": auth_header})

    assert response.status_code == 200, response.text

    response_json = response.json()
    assert response_json == patch_data

    task_in_db = await get_task_by_id(task_id=created_task.id)

    # check that value in DB is actually changed
    for patch_field_name, patch_value in patch_data.items():
        db_value = getattr(task_in_db, patch_field_name)
        if isinstance(db_value, datetime):
            db_value = db_value.isoformat()
        assert db_value == patch_value, "Value in db is not equal to value from request"


@pytest.mark.parametrize(
    "invalid_title",
    (
        "A",  # too short
        "",  # too short
        5,  # can't be number
        get_random_string(length=129),  # too long,
    ),
)
async def test_update_invalid_title_params(
    invalid_title,
    async_client,
    access_token_and_user: tuple[str, GetUser],
    created_task: GetTaskNoForeigns
):
    access_token, _ = access_token_and_user
    auth_header = f"Bearer {access_token}"

    patch_data = {
        "title": invalid_title
    }

    response = await async_client.patch(f"/tasks/{created_task.id}", json=patch_data,
                                        headers={"Authorization": auth_header})

    assert response.status_code == 400, response.text

    task_in_db = await get_task_by_id(task_id=created_task.id)
    assert task_in_db.title != invalid_title, "Title must not be changed after updating with invalid title"
    assert task_in_db.title == created_task.title


@pytest.mark.parametrize(
    "invalid_due_date",
    (
        "A",  # wrong format
        "asdasd",  # wrong format
        "2020-01-01",  # wrong format
        "01-01-2020",  # wrong format,
        2020,  # wrong format
        get_iso_datetime_until_now(days=-5),  # date in past
        get_iso_datetime_until_now(minutes=-1),  # date in past
        get_iso_datetime_until_now(seconds=-2),  # date in past
    ),
)
async def test_update_invalid_due_to_date(
    invalid_due_date,
    async_client,
    access_token_and_user: tuple[str, GetUser],
    created_task: GetTaskNoForeigns
):
    access_token, _ = access_token_and_user
    auth_header = f"Bearer {access_token}"

    patch_data = {
        "due_to_date": invalid_due_date
    }

    response = await async_client.patch(f"/tasks/{created_task.id}", json=patch_data,
                                        headers={"Authorization": auth_header})

    assert response.status_code == 400, response.text

    task_in_db = await get_task_by_id(task_id=created_task.id)
    if task_in_db.due_to_date:
        assert task_in_db.due_to_date.isoformat() != invalid_due_date, "Due date must not be changed after updating with invalid param"
    assert task_in_db.due_to_date == created_task.due_to_date


@pytest.mark.parametrize(
    "invalid_status",
    (
        "A",  # wrong value
        "asdasd",  # wrong value
        "IDEA",  # wrong value
        "IN_PROGRESS",  # wrong value,
        2020,  # wrong value
    ),
)
async def test_update_invalid_status(
    invalid_status,
    async_client,
    access_token_and_user: tuple[str, GetUser],
    created_task: GetTaskNoForeigns
):
    access_token, _ = access_token_and_user
    auth_header = f"Bearer {access_token}"

    patch_data = {
        "status": invalid_status
    }

    response = await async_client.patch(f"/tasks/{created_task.id}", json=patch_data,
                                        headers={"Authorization": auth_header})

    assert response.status_code == 400, response.text

    task_in_db = await get_task_by_id(task_id=created_task.id)
    assert task_in_db.status != invalid_status, "Status must not be changed after updating with invalid param"
    assert task_in_db.status == created_task.status


async def test_success_patch_assignee(
    async_client,
    access_token_and_user: tuple[str, GetUser],
    access_token_and_subscriber: tuple[str, GetUser],
    created_task: GetTaskNoForeigns
):
    access_token, _ = access_token_and_user
    _, subscriber = access_token_and_subscriber
    auth_header = f"Bearer {access_token}"

    patch_data = {
        "assignee_id": subscriber.id,
    }

    response = await async_client.patch(f"/tasks/{created_task.id}", json=patch_data,
                                        headers={"Authorization": auth_header})

    assert response.status_code == 200, response.text
    assert response.json() == patch_data, response.text

    task_in_db = await get_task_by_id(task_id=created_task.id)
    assert task_in_db.assignee_id == subscriber.id


@pytest.mark.parametrize(
    "invalid_assignee_id",
    (
        "asdasd",  # wrong value
        "",  # wrong value
        str(uuid.uuid4()),  # user doesn't exist with such id
        2020,  # wrong value
    ),
)
async def test_update_invalid_assignee_id(
    invalid_assignee_id,
    async_client,
    access_token_and_user: tuple[str, GetUser],
    created_task: GetTaskNoForeigns
):
    access_token, _ = access_token_and_user
    auth_header = f"Bearer {access_token}"

    patch_data = {
        "assignee_id": invalid_assignee_id
    }

    response = await async_client.patch(f"/tasks/{created_task.id}", json=patch_data,
                                        headers={"Authorization": auth_header})

    assert response.status_code == 400, response.text

    task_in_db = await get_task_by_id(task_id=created_task.id)
    assert task_in_db.assignee_id != invalid_assignee_id, "Assignee_id must not be changed after updating with invalid param"
    assert task_in_db.assignee_id == created_task.assignee_id


@pytest.mark.parametrize(
    "patch_data",
    (
        ({"id": str(uuid.uuid4())}),
        ({"id": None}),
        ({"created_at": get_iso_datetime_until_now(days=1)}),
        ({"created_at": None}),
        ({"assigned_at": get_iso_datetime_until_now(days=1)}),
        ({"assigned_at": None}),
        ({"creator_id": None}),
        ({"creator_id": str(uuid.uuid4())}),
        ({"suggested_by_id": str(uuid.uuid4())}),
        ({"suggested_by_id": None}),
    ),
)
async def test_cant_patch_system_fields(
    patch_data,
    async_client,
    access_token_and_user: tuple[str, GetUser],
    created_task: GetTaskNoForeigns
):
    access_token, _ = access_token_and_user
    auth_header = f"Bearer {access_token}"

    response = await async_client.patch(f"/tasks/{created_task.id}", json=patch_data, headers={"Authorization": auth_header})

    assert response.status_code == 400, response.text

    task_in_db = await get_task_by_id(task_id=created_task.id)

    # check that value in DB has not changed
    for patch_field_name in patch_data:
        db_value = getattr(task_in_db, patch_field_name)
        initial_value = getattr(created_task, patch_field_name)
        if isinstance(db_value, datetime):
            db_value = db_value.isoformat()
        assert db_value == initial_value


@pytest.mark.parametrize(
    "patch_data",
    (
        ({"title": "New asd title"}),
        ({"description": "Something"}),
        ({"due_to_date": get_iso_datetime_until_now(days=1)}),
    ),
)
async def test_assignee_cant_change_simple_fields(
    patch_data,
    async_client,
    access_token_and_subscriber: tuple[str, GetUser],
    access_token_and_user: tuple[str, GetUser],
    created_task: GetTaskNoForeigns
):
    #  subscriber is trying to change some fields
    access_token, _ = access_token_and_subscriber
    auth_header = f"Bearer {access_token}"

    response = await async_client.patch(f"/tasks/{created_task.id}", json=patch_data, headers={"Authorization": auth_header})

    assert response.status_code == HTTPStatus.FORBIDDEN, response.text

    task_in_db = await get_task_by_id(task_id=created_task.id)

    # check that value in DB has not changed
    for patch_field_name in patch_data:
        db_value = getattr(task_in_db, patch_field_name)
        initial_value = getattr(created_task, patch_field_name)
        if isinstance(db_value, datetime):
            db_value = db_value.isoformat()
        assert db_value == initial_value


@pytest.mark.parametrize(
    "patch_data",
    (
        ({"title": "New asd title"}),
        ({"description": "Something"}),
        ({"due_to_date": get_iso_datetime_until_now(days=1)}),
        ({"status": TaskStatus.DONE}),
    ),
)
async def test_random_user_cant_change_any_fields(
    patch_data,
    async_client,
    access_token_and_random_user: tuple[str, GetUser],
    access_token_and_user: tuple[str, GetUser],
    created_task: GetTaskNoForeigns
):
    access_token, _ = access_token_and_random_user
    auth_header = f"Bearer {access_token}"

    response = await async_client.patch(f"/tasks/{created_task.id}", json=patch_data, headers={"Authorization": auth_header})

    assert response.status_code == HTTPStatus.FORBIDDEN, response.text

    task_in_db = await get_task_by_id(task_id=created_task.id)

    # check that value in DB has not changed
    for patch_field_name in patch_data:
        db_value = getattr(task_in_db, patch_field_name)
        initial_value = getattr(created_task, patch_field_name)
        if isinstance(db_value, datetime):
            db_value = db_value.isoformat()
        assert db_value == initial_value


async def test_cant_patch_not_existsing_task(
    async_client,
    access_token_and_user: tuple[str, GetUser]
):
    access_token, _ = access_token_and_user
    auth_header = f"Bearer {access_token}"

    patch_data = {
        'title': "Some random title",
    }
    random_task_id = f"{uuid.uuid4()}"

    response = await async_client.patch(f"/tasks/{random_task_id}", json=patch_data,
                                        headers={"Authorization": auth_header})

    assert response.status_code == HTTPStatus.NOT_FOUND, response.text
