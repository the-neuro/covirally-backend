import json
import logging
from datetime import datetime, timezone
from typing import Any

from asyncpg import NotNullViolationError, UniqueViolationError, ForeignKeyViolationError
from databases.backends.postgres import Record
from pydantic import ValidationError
from sqlalchemy import insert, literal_column, select, update, delete

from app.db.base import database
from app.db.models.tasks.schemas import Task, TaskComment
from app.schemas import (
    CreateTask,
    GetTaskNoForeigns,
    CreateTaskComment,
    GetTaskComment,
    TasksFeed,
)


logger = logging.getLogger()


async def create_task(
    create_task_params: CreateTask,
) -> tuple[GetTaskNoForeigns | None, str | None]:
    create_params = create_task_params.dict()

    query = (
        insert(Task)
        .values(create_params)
        .returning(literal_column("id"), literal_column("created_at"))
    )
    transaction = await database.transaction()
    try:
        row: Record = await database.fetch_one(query)

        task_id, created_at = row._mapping.values()
        task: GetTaskNoForeigns = GetTaskNoForeigns.construct(
            **dict(id=task_id, created_at=created_at, **create_params)
        )
    except (NotNullViolationError, UniqueViolationError) as exc:
        logger.error(f"Can't create task: {exc}")
        await transaction.rollback()
        return None, str(exc)
    except ValidationError as exc:
        logger.error(f"Validation error after creating task: {exc}")
        await transaction.rollback()
        return None, str(exc)
    else:
        await transaction.commit()
        return task, None


async def get_task_by_id(task_id: str) -> GetTaskNoForeigns | None:
    query = select(Task).where(Task.id == task_id).limit(1)

    if not (_res := await database.fetch_one(query)):
        return None

    try:
        parsed_task: GetTaskNoForeigns = GetTaskNoForeigns.parse_obj(_res)
    except ValidationError as exc:
        logger.error(f"Can't parse task with {task_id=}, {_res}: {exc}")
        return None
    else:
        return parsed_task


async def update_task(task_id: str, values: dict[str, Any]) -> str | None:
    """
    Returns optional error
    """
    if not values:
        return None

    query = update(Task).where(Task.id == task_id).values(values)
    transaction = await database.transaction()
    try:
        await database.execute(query)
    except (NotNullViolationError, UniqueViolationError) as exc:
        await transaction.rollback()
        return str(exc)
    except ForeignKeyViolationError:
        # no row with such foreign id
        await transaction.rollback()
        return "No row with such foreign key id"
    else:
        await transaction.commit()
        return None


async def add_comment_to_task(
    create_comment_params: CreateTaskComment,
) -> tuple[GetTaskComment | None, str | None]:
    task_id = create_comment_params.task_id
    create_params = create_comment_params.dict()
    create_params["edited"] = False

    query = (
        insert(TaskComment)
        .values(create_params)
        .returning(literal_column("id"), literal_column("created_at"))
    )
    transaction = await database.transaction()
    try:
        row: Record = await database.fetch_one(query)

        comment_id, created_at = row._mapping.values()
        task: GetTaskComment = GetTaskComment.construct(
            **dict(id=comment_id, created_at=created_at, **create_params)
        )

    except (NotNullViolationError, UniqueViolationError) as exc:
        logger.error(f"Can't add comment to {task_id=}: {exc}")
        await transaction.rollback()
        return None, str(exc)
    except ValidationError as exc:
        logger.error(f"Validation error after adding comment to {task_id=}: {exc}")
        await transaction.rollback()
        return None, str(exc)
    else:
        await transaction.commit()
        return task, None


async def comment_exists_in_db(comment_id: str) -> bool:
    query = select([TaskComment.id]).where(TaskComment.id == comment_id).limit(1)
    res: Record = await database.fetch_one(query)
    return bool(res)


async def get_task_comment(comment_id: str) -> GetTaskComment | None:
    query = select(TaskComment).where(TaskComment.id == comment_id).limit(1)

    if not (_res := await database.fetch_one(query)):
        return None

    try:
        parsed_comment: GetTaskComment = GetTaskComment.parse_obj(_res)
    except ValidationError as exc:
        logger.error(f"Can't parse task comment with {comment_id=}, {_res}: {exc}")
        return None
    else:
        return parsed_comment


async def update_task_comment(comment_id: str, values: dict[str, Any]) -> str | None:
    """
    Returns optional error
    """
    if not values:
        return None

    values = values.copy()
    values["edited"] = True
    values["edited_at"] = datetime.now(timezone.utc)

    query = update(TaskComment).where(TaskComment.id == comment_id).values(values)
    transaction = await database.transaction()
    try:
        await database.execute(query)
    except (NotNullViolationError, UniqueViolationError) as exc:
        await transaction.rollback()
        return str(exc)
    except ForeignKeyViolationError:
        # no row with such foreign id
        await transaction.rollback()
        return "No row with such foreign key id"
    else:
        await transaction.commit()
        return None


async def delete_task_comment(comment_id: str) -> None:
    query = delete(TaskComment).where(TaskComment.id == comment_id)
    await database.execute(query)


async def get_feed_tasks(limit: int = 20, offset: int = 0) -> TasksFeed:
    query = """
    SELECT
        json_agg(
            json_build_object(
                'id', tasks.id,
                'title', tasks.title,
                'description', tasks.description,
                'created_at', tasks.created_at,
                'status', tasks.status,
                'creator', json_build_object(
                    'id', creator.id,
                    'username', creator.username,
                    'avatar_url', creator.avatar_url
                )
            ) ORDER BY tasks.created_at DESC
        ) AS tasks
    FROM tasks
    LEFT JOIN users creator ON tasks.creator_id = creator.id
    LIMIT :limit
    OFFSET :offset;
    """
    fetched_data = await database.fetch_one(
        query, values={"limit": limit, "offset": offset}
    )
    res: TasksFeed = TasksFeed.parse_obj({"tasks": json.loads(fetched_data["tasks"])})
    return res
