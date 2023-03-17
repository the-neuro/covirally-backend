import logging

from sqlalchemy import delete, select

from sqlalchemy.dialects.postgresql import insert

from app.db.base import database
from app.db.models.hashtags.schemas import Hashtag
from app.schemas import TaskHashtags


logger = logging.getLogger()


async def add_hashtags(tags: list[str], task_id: str) -> None:
    """
    Remove all hastags for task
    And then insert new ones
    """
    data = [{"task_id": task_id, "hashtag": tag} for tag in tags]

    insert_query = insert(Hashtag)
    delete_query = delete(Hashtag).where(Hashtag.task_id == task_id)
    async with database.transaction():
        await database.execute(delete_query)
        await database.execute_many(insert_query, data)


async def get_hashtags_for_task(task_id: str) -> TaskHashtags:
    query = select(Hashtag.id, Hashtag.hashtag).where(Hashtag.task_id == task_id)
    fetched_data = await database.fetch_all(query)
    res: TaskHashtags = TaskHashtags.parse_obj({"hashtags": fetched_data})
    return res
