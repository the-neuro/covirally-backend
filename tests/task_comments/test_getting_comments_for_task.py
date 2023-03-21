import asyncio
from http import HTTPStatus

import pytest

from app.api.auth.password_utils import get_password_hash
from app.db.models.tasks.handlers import create_task, add_comment_to_task
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


@pytest.fixture(scope="module")
async def task_with_20_comments(access_token_and_user) -> GetTaskNoForeigns:
    _, user = access_token_and_user

    data = {
        "title": "Hello",
        "description": "Some description",
        "creator_id": user.id,
    }
    task, _ = await create_task(CreateTask.construct(**data))
    for i in range(20):
        await add_comment_to_task(
            create_comment_params=CreateTaskComment(
                content=f"{COMMENT_CONTENT}_{i}",
                task_id=task.id,
                user_id=user.id
            )
        )
    return task


async def test_get_zero_comments(async_client, access_token_and_user, task_without_comments):
    access_token, _ = access_token_and_user
    auth_header = f"Bearer {access_token}"

    task_id = task_without_comments.id
    size = 10
    response = await async_client.get(f"/tasks/{task_id}/comments?size={size}", headers={"Authorization": auth_header})

    assert response.status_code == 200, response.text
    assert response.json() == {'items': [], 'total': 0, 'page': 1, 'size': size, 'pages': 0}


async def test_get_one_comment(async_client, access_token_and_user: tuple[str, GetUser], task_with_one_comment: GetTaskNoForeigns):
    access_token, user = access_token_and_user
    auth_header = f"Bearer {access_token}"

    task_id = task_with_one_comment.id
    size = 10
    response = await async_client.get(f"/tasks/{task_id}/comments?size={size}",
                                      headers={"Authorization": auth_header})

    assert response.status_code == 200, response.text
    response_json = response.json()

    assert response_json['page'] == 1
    assert response_json['pages'] == 1
    assert response_json['size'] == size
    assert response_json['total'] == 1

    # only one comment in response
    assert len(response_json['items']) == 1
    comment = response_json['items'][0]
    assert comment['content'] == COMMENT_CONTENT
    assert comment['edited'] is False
    assert comment['edited_at'] is None
    assert comment['user'] == {
        'avatar_url': None,
        'id': user.id,
        'username': user.username,
    }


async def test_get_multiple_comments(async_client, access_token_and_user: tuple[str, GetUser], task_with_20_comments: GetTaskNoForeigns):
    access_token, user = access_token_and_user
    auth_header = f"Bearer {access_token}"

    task_id, size = task_with_20_comments.id, 10

    # get first page
    url = f"/tasks/{task_id}/comments?size={size}&page=1"
    response = await async_client.get(url, headers={"Authorization": auth_header})
    assert response.status_code == 200, response.text
    response_json = response.json()
    assert response_json['page'] == 1
    assert response_json['pages'] == 2
    assert response_json['size'] == size
    assert response_json['total'] == 20

    # on page must be size elements
    assert len(response_json['items']) == size
    for i, comment in enumerate(response_json['items']):
        assert comment['content'] == f"{COMMENT_CONTENT}_{i}"
        assert comment['edited'] is False
        assert comment['edited_at'] is None
        assert comment['user'] == {
            'avatar_url': None,
            'id': user.id,
            'username': user.username,
        }

    # get second page with 10 elements
    url = f"/tasks/{task_id}/comments?size={size}&page=2"
    response = await async_client.get(url, headers={"Authorization": auth_header})
    assert response.status_code == 200, response.text
    response_json = response.json()
    assert response_json['page'] == 2
    assert response_json['pages'] == 2
    assert response_json['size'] == size
    assert response_json['total'] == 20
    assert len(response_json['items']) == size

    # get third page with no elements
    url = f"/tasks/{task_id}/comments?size={size}&page=3"
    response = await async_client.get(url, headers={"Authorization": auth_header})
    assert response.status_code == 200, response.text
    response_json = response.json()
    assert response_json['page'] == 3
    assert response_json['pages'] == 2
    assert response_json['size'] == size
    assert response_json['total'] == 20
    assert len(response_json['items']) == 0


async def test_cant_get_comments_while_unauthorized(async_client, task_with_20_comments, task_with_one_comment, task_without_comments):
    for task in (task_without_comments, task_with_one_comment, task_with_20_comments):
        response = await async_client.get(f"/tasks/{task.id}/comments")
        assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text
