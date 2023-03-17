import uuid
from datetime import datetime, timezone, timedelta
from http import HTTPStatus

import pytest
from jose import jwt

from app.api.auth.password_utils import get_password_hash
from app.api.auth.utils import create_access_token, ALGORITHM
from app.config import settings
from app.db.models.tasks.handlers import create_task, add_comment_to_task, \
    get_task_comment
from app.db.models.users.handlers import create_user
from app.schemas import GetUser, CreateUser, GetTaskNoForeigns, CreateTask, \
    GetTaskComment, CreateTaskComment
from tests.utils import get_iso_datetime_until_now

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
async def access_token_and_user(async_client) -> tuple[str, GetUser]:
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
async def access_token_and_random_user(async_client) -> tuple[str, GetUser]:
    """
    Create user, authorize it and get access token with username
    """
    email, password = "sjxb@apple.com", "aglafknaf"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "bmboan",
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
async def created_task(access_token_and_user) -> GetTaskNoForeigns:
    _, user = access_token_and_user
    data = {
        "title": "Hello",
        "description": "Some description",
        "creator_id": user.id,
    }
    task, _ = await create_task(CreateTask.construct(**data))
    return task


@pytest.fixture(scope="function")
async def created_comment(
    access_token_and_user, created_task: GetTaskNoForeigns
) -> GetTaskComment:
    _, user = access_token_and_user
    data = CreateTaskComment(
        content="Some content",
        task_id=created_task.id,
        user_id=user.id,
    )
    comment, _ = await add_comment_to_task(data)
    return comment


async def test_success_update_comment(
    async_client, access_token_and_user, created_comment: GetTaskComment
):
    access_token, _ = access_token_and_user
    auth_header = f"Bearer {access_token}"

    data = {
        "content": "New content",
    }
    url = f"/tasks/comment/{created_comment.id}"

    response = await async_client.patch(url, json=data, headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.OK, response.text

    response_json = response.json()
    assert response_json == data, response.text

    comment_in_db = await get_task_comment(comment_id=created_comment.id)
    assert comment_in_db is not None

    assert comment_in_db.content == data["content"]
    assert comment_in_db.edited is True

    # check that edited_at was set
    two_seconds_before = datetime.now(timezone.utc) - timedelta(seconds=2)
    two_seconds_after = datetime.now(timezone.utc) + timedelta(seconds=2)
    assert two_seconds_before < comment_in_db.edited_at < two_seconds_after


@pytest.mark.parametrize(
    "update_data",
    (
        ({"content": ""}),
        ({"content": " "}),
        ({"content": "     "}),
    ),
)
async def test_update_invalid_params(async_client, access_token_and_user, created_comment: GetTaskComment, update_data):
    access_token, _ = access_token_and_user
    auth_header = f"Bearer {access_token}"

    url = f"/tasks/comment/{created_comment.id}"
    response = await async_client.patch(url, json=update_data,headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.BAD_REQUEST, response.text

    comment_in_db = await get_task_comment(comment_id=created_comment.id)
    assert comment_in_db.content == created_comment.content


async def test_random_user_cant_update_comment(async_client, access_token_and_random_user, created_comment: GetTaskComment):
    access_token, _ = access_token_and_random_user
    auth_header = f"Bearer {access_token}"

    data = {
        "content": "New content from random user",
    }
    url = f"/tasks/comment/{created_comment.id}"
    response = await async_client.patch(url, json=data,
                                        headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.FORBIDDEN, response.text

    # ensure that data in db hasn't changed
    comment_in_db = await get_task_comment(comment_id=created_comment.id)
    assert comment_in_db.content == created_comment.content


@pytest.mark.parametrize(
    "system_fields",
    (
        ({"id": str(uuid.uuid4())}),
        ({"task_id": str(uuid.uuid4())}),
        ({"user_id": str(uuid.uuid4())}),
        ({"edited": False}),
        ({"edited_at": get_iso_datetime_until_now(days=2)}),
        ({"created_at": get_iso_datetime_until_now(days=2)}),
    ),
)
async def test_cant_update_system_fields(async_client, access_token_and_user, created_comment: GetTaskComment, system_fields):
    access_token, _ = access_token_and_user
    auth_header = f"Bearer {access_token}"

    url = f"/tasks/comment/{created_comment.id}"
    response = await async_client.patch(url, json=system_fields, headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.BAD_REQUEST, response.text

    comment_in_db = await get_task_comment(comment_id=created_comment.id)
    for field in ("id", "task_id", "user_id", "edited", "edited_at", "created_at"):
        assert getattr(comment_in_db, field) == getattr(created_comment, field)


async def test_update_comment_while_unauthorized(async_client, created_comment: GetTaskComment):
    url = f"/tasks/comment/{created_comment.id}"
    response = await async_client.patch(url)
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_update_comment_with_wrong_email(async_client, created_comment: GetTaskComment):
    # create access token with wrong email
    access_token = create_access_token(email="ldvdfs@gmail.com")
    auth_header = f"Bearer {access_token}"

    url = f"/tasks/comment/{created_comment.id}"
    response = await async_client.patch(url, json={'content': 'New one'}, headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_update_comment_with_wrong_params_in_payload(async_client, created_comment: GetTaskComment):
    # leave payload empty
    token: str = jwt.encode({}, settings.secret_jwt_token, algorithm=ALGORITHM)

    auth_header = f"Bearer {token}"

    url = f"/tasks/comment/{created_comment.id}"
    response = await async_client.patch(url, headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_update_comment_with_random_access_token(async_client, created_comment: GetTaskComment):
    auth_header = f"Bearer {uuid.uuid4()}"

    url = f"/tasks/comment/{created_comment.id}"
    response = await async_client.patch(url, headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text
