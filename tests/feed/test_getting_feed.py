from http import HTTPStatus

import pytest

from app.api.auth.password_utils import get_password_hash
from app.db.models.tasks.task_handlers import create_task
from app.db.models.tasks.comment_handlers import add_comment_to_task
from app.db.models.users.handlers import create_user
from app.schemas import GetUser, CreateUser, GetTaskNoForeigns, CreateTask, \
    CreateTaskComment


pytestmark = pytest.mark.asyncio


COMMENT_CONTENT = "content"


@pytest.fixture(scope="module")
async def access_token_and_user(async_client) -> tuple[str, GetUser]:
    """
    Create user, authorize it and get access token with username
    """
    email, password = "sjvas1b@apple.com", "aglafknaf"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "appleappmdass",
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
async def task_without_comments(access_token_and_user) -> GetTaskNoForeigns:
    _, user = access_token_and_user

    data = {
        "title": "Hello",
        "description": "Some description",
        "creator_id": user.id,
    }
    task, _ = await create_task(CreateTask.construct(**data))
    return task


@pytest.fixture(scope="module")
async def task_with_one_comment(access_token_and_user) -> GetTaskNoForeigns:
    _, user = access_token_and_user

    data = {
        "title": "Hello",
        "description": "Some description",
        "creator_id": user.id,
    }
    task, _ = await create_task(CreateTask.construct(**data))
    await add_comment_to_task(
        create_comment_params=CreateTaskComment(
            content=COMMENT_CONTENT,
            task_id=task.id,
            user_id=user.id
        )
    )
    return task


async def test_get_paginated_feed(
    async_client,
    access_token_and_user: tuple[str, GetUser],
    task_without_comments: GetTaskNoForeigns,
    task_with_one_comment: GetTaskNoForeigns,
):
    access_token, user = access_token_and_user
    auth_header = f"Bearer {access_token}"

    page_size = 20
    task_data = {
        "title": "Hello",
        "description": "Some description",
        "creator_id": user.id,
    }
    for i in range(20):
        await create_task(CreateTask.construct(**task_data))

    # get first page
    response = await async_client.get(f"/feed?page=1&size={page_size}", headers={"Authorization": auth_header})
    assert response.status_code == 200, response.text
    response_json = response.json()

    assert response_json['page'] == 1
    assert response_json['pages'] == 2
    assert response_json['size'] == page_size
    assert response_json['total'] == 22  # 20 created here and two above
    items_from_first_page: list = response_json['items']
    assert len(items_from_first_page) == 20

    # get second page
    response = await async_client.get(f"/feed?page=2&size={page_size}", headers={"Authorization": auth_header})
    assert response.status_code == 200, response.text
    response_json = response.json()

    assert response_json['page'] == 2
    assert response_json['pages'] == 2
    assert response_json['size'] == page_size
    assert response_json['total'] == 22  # 20 created here and two above
    items_from_second_page: list = response_json['items']
    assert len(items_from_second_page) == 2

    all_items = items_from_first_page + items_from_second_page
    must_be_fields = ('id', 'title', 'description', 'created_at', 'status', 'creator', 'n_comments')
    for task in all_items:
        assert len(task) == len(must_be_fields), f"Unexpected field in response: {task}"
        for field in must_be_fields:
            assert field in task
        assert task['creator'] == {
            'id': user.id,
            'username': user.username,
            'avatar_url': user.avatar_url,
        }

        # check number of comments
        if task['id'] == task_without_comments.id:
            assert task['n_comments'] == 0
        elif task['id'] == task_with_one_comment.id:
            assert task['n_comments'] == 1


async def test_can_get_feed_while_unauthorized(async_client):
    response = await async_client.get("/feed")
    assert response.status_code == HTTPStatus.OK, response.text
