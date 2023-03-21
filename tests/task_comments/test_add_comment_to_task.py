import uuid
from http import HTTPStatus

import pytest
from jose import jwt

from app.api.auth.password_utils import get_password_hash
from app.api.auth.utils import create_access_token, ALGORITHM
from app.config import settings
from app.db.models.tasks.task_handlers import create_task
from app.db.models.tasks.comment_handlers import comment_exists_in_db
from app.db.models.users.handlers import create_user
from app.schemas import CreateUser, GetTaskNoForeigns, GetUser, CreateTask
from tests.utils import get_random_string

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
async def access_token_and_user(async_client) -> tuple[str, GetUser]:
    """
    Create user, authorize it and get access token with username
    """
    email, password = "sjvas12daxb@apple.com", "aglafknaf"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "appleapplevmds",
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
async def random_user(async_client) -> GetUser:
    """
    Create random user, authorize it and get access token with username
    """
    email = "sjvafdlbvdfsas@apvfdple.com"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "applebnris12",
        "password": get_password_hash("amlavskdfvalf"),
        "email": email,
        "email_is_verified": True,
    }
    user, _ = await create_user(CreateUser.construct(**user_data))
    return user


@pytest.fixture(scope="function")
async def created_task(access_token_and_user) -> GetTaskNoForeigns:
    """Scope is function => new task is created per each test"""
    _, user = access_token_and_user

    data = {
        "title": "Hello",
        "description": "Some description",
        "creator_id": user.id,
    }
    task, _ = await create_task(CreateTask.construct(**data))
    return task


@pytest.mark.parametrize(
    "comment_data",
    (
        ({"content": "Some content"}),
        ({"content": get_random_string(length=250)}),
        ({"content": get_random_string(length=2000)}),
    ),
)
async def test_success_add_comment_to_task(async_client, comment_data, access_token_and_user, created_task: GetTaskNoForeigns):
    access_token, user = access_token_and_user

    data = {
        'task_id': created_task.id,
        'user_id': user.id,
        **comment_data
    }

    auth_header = f"Bearer {access_token}"
    response = await async_client.post("/tasks/comment", json=data, headers={"Authorization": auth_header})

    assert response.status_code == HTTPStatus.CREATED, response.text
    response_json = response.json()

    assert 'id' in response_json, response.text
    assert 'created_at' in response_json, response.text

    assert response_json['task_id'] == data['task_id']
    assert response_json['user_id'] == data['user_id']
    assert response_json['edited'] is False
    assert response_json['edited_at'] is None

    comment_in_db = await comment_exists_in_db(comment_id=response_json['id'])
    assert comment_in_db is True


async def test_create_comment_with_another_user_id(async_client, access_token_and_user, random_user: GetUser, created_task: GetTaskNoForeigns):
    # authorize one user and trying to put in payload another user_id
    access_token, _ = access_token_and_user

    data = {
        'task_id': created_task.id,
        'user_id': random_user.id,
        "content": "Some content",
    }
    auth_header = f"Bearer {access_token}"
    response = await async_client.post("/tasks/comment", json=data, headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.BAD_REQUEST, response.text


@pytest.mark.parametrize(
    "comment_data",
    (
        ({"content": ""}),
        ({"content": " "}),
        ({"content": "     "}),
        ({"content": get_random_string(2001)}),
    ),
)
async def test_invalid_data_for_comment(async_client, comment_data, access_token_and_user, created_task):
    access_token, user = access_token_and_user

    data = {
        'task_id': created_task.id,
        'user_id': user.id,
        **comment_data
    }

    auth_header = f"Bearer {access_token}"
    response = await async_client.post("/tasks/comment", json=data, headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.BAD_REQUEST, response.text


async def test_add_comment_while_unauthorized(async_client):
    response = await async_client.post("/tasks/comment")
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_add_comment_with_wrong_email_payload(async_client):
    # create access token with wrong email
    access_token = create_access_token(email="ldvdfs@gmail.com")
    auth_header = f"Bearer {access_token}"

    response = await async_client.post("/tasks/comment", headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_add_comment_with_wrong_params_in_payload(async_client):
    # leave payload empty
    token: str = jwt.encode({}, settings.secret_jwt_token, algorithm=ALGORITHM)

    auth_header = f"Bearer {token}"

    response = await async_client.post("/tasks/comment", headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text


async def test_add_comment_with_random_access_token(async_client):
    auth_header = f"Bearer {uuid.uuid4()}"

    response = await async_client.post("/tasks/comment", headers={"Authorization": auth_header})
    assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text
