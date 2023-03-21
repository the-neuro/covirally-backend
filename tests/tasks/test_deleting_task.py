import uuid
from http import HTTPStatus

import pytest

from app.api.auth.password_utils import get_password_hash
from app.db.models.hashtags.handlers import add_hashtags, get_hashtags_for_task
from app.db.models.tasks.task_handlers import create_task, get_task_by_id
from app.db.models.tasks.comment_handlers import add_comment_to_task, \
    get_total_count_of_comment_for_task
from app.db.models.users.handlers import create_user
from app.schemas import GetUser, CreateUser, CreateTask, GetTaskNoForeigns, \
    CreateTaskComment

pytestmark = pytest.mark.asyncio


HASHTAGS = ["asdas", "m2d"]
COMMENTS = ("alsdkasd", "12pncsd")


@pytest.fixture(scope="module")
async def access_token_and_user(async_client) -> tuple[str, GetUser]:
    """
    Create user, authorize it and get access token with username
    """
    email, password = "sjvas@apple.com", "asdas"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "appleapple",
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
async def access_token_and_random_user(async_client) -> tuple[str, GetUser]:
    """
    Create user, authorize it and get access token with username
    """
    email, password = "sjvascdsk1@apple.com", "asdas"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "appcsd2msle",
        "password": get_password_hash(password),
        "email": email,
        "email_is_verified": True,
    }
    user, _ = await create_user(CreateUser.construct(**user_data))

    auth_data = {"username": email, "password": password}
    auth_response = await async_client.post("/auth/token", data=auth_data)

    access_token = auth_response.json()["access_token"]
    return access_token, user


@pytest.fixture(scope="function")
async def task(access_token_and_user) -> GetTaskNoForeigns:
    """Scope is function => new task is created per each test"""
    _, user = access_token_and_user

    data = {
        "title": "Hello",
        "description": "Some description",
        "creator_id": user.id,
    }
    task_, _ = await create_task(CreateTask.construct(**data))

    await add_hashtags(tags=HASHTAGS, task_id=task_.id)
    for comment in COMMENTS:
        await add_comment_to_task(
            create_comment_params=CreateTaskComment(
                content=comment,
                task_id=task_.id,
                user_id=user.id
            )
        )
    return task_


async def test_success_delete(async_client, access_token_and_user, task: GetTaskNoForeigns):
    access_token, _ = access_token_and_user
    auth_header, url = f"Bearer {access_token}", f"/tasks/{task.id}"

    task_in_db_before = await get_task_by_id(task.id)
    assert task_in_db_before is not None

    hashtags_before = await get_hashtags_for_task(task.id)
    assert len(hashtags_before.hashtags) == len(HASHTAGS)

    total_comments_before = await get_total_count_of_comment_for_task(task.id)
    assert total_comments_before == len(COMMENTS)

    # delete task request
    response = await async_client.delete(url, headers={"Authorization": auth_header})
    assert response.status_code == 200

    task_id_db = await get_task_by_id(task.id)
    assert task_id_db is None, "Task is not removed from DB."

    hashtags = await get_hashtags_for_task(task.id)
    assert len(hashtags.hashtags) == 0, "Hashtags are not deleted"

    total_comments = await get_total_count_of_comment_for_task(task.id)
    assert total_comments == 0, "Comments are not deleted"


async def test_delete_while_unauthorized(
    async_client, access_token_and_user, task: GetTaskNoForeigns
):
    response = await async_client.delete(f"/tasks/{task.id}")
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    task_id_db = await get_task_by_id(task.id)
    assert task_id_db is not None, "Task must not be deleted when user is not authorized"

    hashtags = await get_hashtags_for_task(task.id)
    assert len(hashtags.hashtags) == len(HASHTAGS), "Hashtags must not be deleted"

    total_comments = await get_total_count_of_comment_for_task(task.id)
    assert total_comments == len(COMMENTS), "Comments must not be deleted"


async def test_delete_someone_elses_task(async_client, access_token_and_random_user, task: GetTaskNoForeigns):
    """
    User is trying to delete someone else's task
    """
    access_token, _ = access_token_and_random_user
    auth_header, url = f"Bearer {access_token}", f"/tasks/{task.id}"

    # delete task request
    response = await async_client.delete(url, headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.FORBIDDEN

    # task is not deleted
    task_id_db = await get_task_by_id(task.id)
    assert task_id_db is not None

    hashtags = await get_hashtags_for_task(task.id)
    assert len(hashtags.hashtags) == len(HASHTAGS), "Hashtags must not be deleted"

    total_comments = await get_total_count_of_comment_for_task(task.id)
    assert total_comments == len(COMMENTS), "Comments must not be deleted"


async def test_delete_not_exist_task(async_client, access_token_and_user):
    access_token, _ = access_token_and_user
    auth_header = f"Bearer {access_token}"

    task_id = str(uuid.uuid4())
    response = await async_client.delete(f"/tasks/{task_id}", headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.NOT_FOUND
