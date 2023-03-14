from collections import Counter

import pytest

from app.db.models.hashtags.handlers import get_hashtags_for_task
from app.db.models.hashtags.utils import extract_and_insert_hashtags
from app.db.models.tasks.handlers import create_task
from app.db.models.users.handlers import create_user
from app.schemas import CreateUser, GetUser, GetTaskNoForeigns, CreateTask

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
async def creator(async_client) -> GetUser:
    """
    Create user, authorize it and get access token with username
    """
    email = "sjvas@apple.com"
    user_data = {
        "first_name": "Steve",
        "last_name": "Jobs",
        "username": "appleapple",
        "password": "asdkadfs",
        "email": email,
        "email_is_verified": True,
    }
    user, _ = await create_user(CreateUser.construct(**user_data))
    return user


@pytest.fixture(scope="function")
async def created_task(async_client, creator: GetUser) -> GetTaskNoForeigns:
    """Scope is function => new task is created per each test"""
    data = CreateTask(
        title="Hello",
        description="Some description",
        creator_id=creator.id,
    )

    task, _ = await create_task(data)
    return task


async def test_hashtags_are_inserted(created_task: GetTaskNoForeigns):
    _valid_hashtags = ['asd', "mvm", "_09as", "vslakvaldkvnaflv", "alfkbn201n2d", "ADAS9124_0-asd"]
    valid_hashtags = " ".join((f"#{tag}" for tag in _valid_hashtags))

    _invalid_hashtags = ['<AS-', "vm_=1", "*12x", "asddsjfgajfgalkjef123", "mvsd$@", "@dasd#"]
    invalid_hashtags = " ".join((f"#{tag}" for tag in _invalid_hashtags))

    text = '\n'.join([valid_hashtags, invalid_hashtags])
    await extract_and_insert_hashtags(text, task_id=created_task.id)

    db_hashtags = await get_hashtags_for_task(created_task.id)
    db_hashtags = db_hashtags.hashtags
    hashtags_from_db = [tag.hashtag for tag in db_hashtags]

    valid_hashtags = [tag.lower() for tag in _valid_hashtags]

    assert Counter(valid_hashtags) == Counter(hashtags_from_db)
