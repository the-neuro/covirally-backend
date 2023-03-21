from datetime import datetime, timezone, timedelta
from http import HTTPStatus
from uuid import uuid4

import pytest

from app.api.auth.password_utils import get_password_hash
from app.db.models.tasks.task_handlers import create_task
from app.db.models.tasks.comment_handlers import add_comment_to_task
from app.db.models.users.handlers import create_user
from app.schemas import GetUser, CreateUser, GetTaskNoForeigns, CreateTask, \
    CreateTaskComment
from tests.utils import get_iso_datetime_until_now

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
async def access_token_and_creator(async_client) -> tuple[str, GetUser]:
    """
    Create user, authorize it and get access token with username
    """
    email, password = "sjvas12davxb@apple.com", "aglafknaf"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "appleapplevmdass",
        "password": get_password_hash(password),
        "email": email,
        "email_is_verified": True,
    }
    user, _ = await create_user(CreateUser.construct(**user_data))

    auth_data = {"username": email, "password": password}
    auth_response = await async_client.post("/auth/token", data=auth_data)

    access_token = auth_response.json()["access_token"]
    return access_token, user


@pytest.fixture(scope="module")
async def access_token_and_user(async_client) -> tuple[str, GetUser]:
    """
    Create user, authorize it and get access token with username
    """
    email, password = "svz2asvxb@apple.com", "aglafknaf"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "apbopmacnass",
        "password": get_password_hash(password),
        "email": email,
        "email_is_verified": True,
    }
    user, _ = await create_user(CreateUser.construct(**user_data))

    auth_data = {"username": email, "password": password}
    auth_response = await async_client.post("/auth/token", data=auth_data)

    access_token = auth_response.json()["access_token"]
    return access_token, user


@pytest.fixture(scope="module")
async def created_task(access_token_and_creator, access_token_and_user) -> GetTaskNoForeigns:
    _, creator = access_token_and_creator
    _, user = access_token_and_user
    data = CreateTask(
        title="Hello",
        description="Some description",
        creator_id=creator.id,
        assignee_id=user.id,
        due_to_date=get_iso_datetime_until_now(days=2),
        suggested_by_id=user.id,
    )
    task, _ = await create_task(data)
    await add_comment_to_task(
        create_comment_params=CreateTaskComment(
            content="some",
            task_id=task.id,
            user_id=user.id
        )
    )
    return task


async def test_success_get_by_creator(
    async_client, access_token_and_creator: tuple[str, GetUser],
    access_token_and_user: tuple[str, GetUser], created_task: GetTaskNoForeigns
):
    """
    Creator can get access to assignee, suggested_by and due_to_date info
    """
    access_token, creator = access_token_and_creator
    _, user = access_token_and_user
    auth_header = f"Bearer {access_token}"

    response = await async_client.get(f"/tasks/{created_task.id}", headers={"Authorization": auth_header})
    assert response.status_code == 200, response.text
    json_response = response.json()

    assert json_response['title'] == created_task.title
    assert json_response['description'] == created_task.description
    assert json_response['status'] == created_task.status
    assert json_response['creator'] == {
        "id": creator.id,
        "username": creator.username,
        "avatar_url": creator.avatar_url,
    }
    assert json_response['n_comments'] == 1

    assert json_response['created_at'] is not None
    if created_task.assignee_id:
        assert json_response['assignee'] == {
            "id": user.id,
            "username": user.username,
            "avatar_url": user.avatar_url,
        }
        assert json_response['assigned_at'] is not None
    if created_task.due_to_date:
        assert json_response['due_to_date'] is not None
    if created_task.suggested_by_id:
        assert json_response['suggested_by'] == {
            "id": user.id,
            "username": user.username,
            "avatar_url": user.avatar_url,
        }


async def test_success_get_by_user(
    async_client, access_token_and_creator: tuple[str, GetUser],
    access_token_and_user: tuple[str, GetUser], created_task: GetTaskNoForeigns
):
    """
    regular user can't get info about assignee, suggested_by and due_to_date
    """
    access_token, _ = access_token_and_user
    _, creator = access_token_and_creator
    auth_header = f"Bearer {access_token}"

    response = await async_client.get(f"/tasks/{created_task.id}", headers={"Authorization": auth_header})
    assert response.status_code == 200, response.text
    json_response = response.json()

    assert json_response['title'] == created_task.title
    assert json_response['description'] == created_task.description
    assert json_response['status'] == created_task.status
    assert json_response['creator'] == {
        "id": creator.id,
        "username": creator.username,
        "avatar_url": creator.avatar_url,
    }
    assert json_response['n_comments'] == 1

    assert json_response['created_at'] is not None
    if created_task.assignee_id:
        assert json_response['assignee'] is None, "Regular user cant see assignee info"
        assert json_response['assigned_at'] is None, "Regular user cant see assigned_at info"
    if created_task.due_to_date:
        assert json_response['due_to_date'] is None, "Regular user cant see due_to_date info"
    if created_task.suggested_by_id:
        assert json_response['suggested_by'] is None, "Regular user cant see suggested_by info"


async def test_get_non_existing_task(async_client, access_token_and_user: tuple[str, GetUser]):
    access_token, _ = access_token_and_user
    auth_header = f"Bearer {access_token}"

    response = await async_client.get(f"/tasks/{uuid4()}", headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.NOT_FOUND, response.text


async def test_get_task_while_not_authorized(async_client, access_token_and_creator, created_task: GetTaskNoForeigns):
    response = await async_client.get(f"/tasks/{created_task.id}")
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_with_wrong_auth_token(async_client, access_token_and_creator, created_task: GetTaskNoForeigns):
    headers = {"Authorization": "some token"}
    response = await async_client.get(f"/tasks/{created_task.id}", headers=headers)
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text
