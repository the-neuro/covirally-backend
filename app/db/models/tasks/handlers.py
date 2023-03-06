import logging
from typing import Any

from asyncpg import NotNullViolationError, UniqueViolationError, ForeignKeyViolationError
from databases.backends.postgres import Record
from pydantic import ValidationError
from sqlalchemy import insert, literal_column, select, update

from app.db.base import database
from app.db.models.tasks.schemas import Task
from app.schemas import CreateTask, GetTaskNoForeigns


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
