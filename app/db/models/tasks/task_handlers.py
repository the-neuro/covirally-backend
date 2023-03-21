import asyncio
import json
import logging
from typing import Any
from math import ceil

from asyncpg import NotNullViolationError, UniqueViolationError, ForeignKeyViolationError
from databases.backends.postgres import Record
from fastapi_pagination import Page
from pydantic import ValidationError
from sqlalchemy import insert, literal_column, select, update, delete

from app.db.base import database
from app.db.models.hashtags.schemas import Hashtag
from app.db.models.tasks.comment_handlers import get_total_count_of_comment_for_task
from app.db.models.tasks.schemas import Task, TaskComment
from app.schemas import (
    CreateTask,
    GetTaskNoForeigns,
    GetTask,
    TaskFeed,
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


async def delete_task(task_id: str) -> str | None:
    delete_hashtag_query = delete(Hashtag).where(Hashtag.task_id == task_id)
    delete_comments_query = delete(TaskComment).where(TaskComment.task_id == task_id)
    delete_task_query = delete(Task).where(Task.id == task_id)

    transaction = await database.transaction()
    try:
        await database.execute(delete_hashtag_query)
        await database.execute(delete_comments_query)
        await database.execute(delete_task_query)
    except Exception as exc:  # pylint: disable=broad-except
        err = f"Can't delete {task_id=}: {exc}"
        logger.error(err)
        await transaction.rollback()
        return err
    else:
        await transaction.commit()
        return None


async def get_total_counf_of_tasks() -> int:
    # todo: cache this value

    query = "SELECT COUNT(*) FROM tasks"
    res: int = await database.fetch_val(query)
    return res


async def get_joined_task(task_id: str) -> GetTask | None:
    query = """
    SELECT
        tasks.id,
        tasks.creator_id,
        tasks.title,
        tasks.description,
        tasks.status,
        tasks.due_to_date,
        tasks.assigned_at,
        tasks.created_at,
        jsonb_build_object(
            'id', creator.id,
            'username', creator.username,
            'avatar_url', creator.avatar_url
        ) as creator,
        CASE
            WHEN tasks.assignee_id IS NULL THEN NULL
            ELSE
                jsonb_build_object(
                    'id', assignee.id,
                    'username', assignee.username,
                    'avatar_url', assignee.avatar_url
                )
        END assignee,
        CASE
            WHEN tasks.suggested_by_id IS NULL THEN NULL
            ELSE
                jsonb_build_object(
                    'id', suggested_by.id,
                    'username', suggested_by.username,
                    'avatar_url', suggested_by.avatar_url
                )
        END suggested_by
    FROM tasks
    LEFT JOIN users creator on tasks.creator_id = creator.id
    LEFT JOIN users assignee on tasks.assignee_id = assignee.id
    LEFT JOIN users suggested_by on tasks.suggested_by_id = suggested_by.id
    WHERE tasks.id=:task_id;
    """
    fetched_data: Record | None
    fetched_data, n_comments = await asyncio.gather(
        *(
            database.fetch_one(query, values={"task_id": task_id}),
            get_total_count_of_comment_for_task(task_id),
        )
    )
    data: GetTask | None = None
    if fetched_data:
        _data = dict(fetched_data._mapping.items(), n_comments=n_comments)
        data = GetTask.parse_obj(_data)
    return data


async def get_feed_tasks(page: int, size: int) -> Page[TaskFeed]:
    query = """
    WITH tasks_with_comment_count AS (
        SELECT
            tasks.id,
            count(tc.*) as comments_count
        FROM tasks
        LEFT JOIN tasks_comments tc on tasks.id = tc.task_id
        GROUP BY 1
        LIMIT :limit
        OFFSET :offset
    ),
    table_with_json_rows AS (
        SELECT
            json_build_object(
                'id', tasks.id,
                'title', tasks.title,
                'description', tasks.description,
                'created_at', tasks.created_at,
                'status', tasks.status,
                'n_comments', tcc.comments_count,
                'creator', json_build_object(
                     'id', creator.id,
                     'username', creator.username,
                     'avatar_url', creator.avatar_url
                )
            ) AS _tasks
        FROM tasks_with_comment_count tcc
        LEFT JOIN tasks ON tcc.id = tasks.id
        LEFT JOIN users creator ON tasks.creator_id = creator.id
        ORDER BY tasks.created_at DESC
    )
    SELECT json_agg(_tasks) tasks from table_with_json_rows;
    """
    values = {"limit": size, "offset": (page - 1) * size}
    fetched_tasks, total = await asyncio.gather(
        *(
            database.fetch_one(query, values),
            get_total_counf_of_tasks(),
        )
    )
    if not fetched_tasks or not fetched_tasks["tasks"]:
        tasks = []
    else:
        _dict_tasks = json.loads(fetched_tasks["tasks"])
        tasks = [TaskFeed.parse_obj(task) for task in _dict_tasks]

    total_pages = ceil(total / size)
    return Page(total=total, page=page, size=size, items=tasks, pages=total_pages)
