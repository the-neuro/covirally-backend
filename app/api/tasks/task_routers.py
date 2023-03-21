import asyncio
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import UUID4
from starlette.responses import JSONResponse

from app.api.auth.utils import get_current_user
from app.api.errors import (
    BadRequestCreatingTask,
    InvalidCreatorSuggesterIds,
    BadRequestUpdatingTask,
    TaskNotFound,
    NotCreatorPermissionError,
    BadRequestDeletingTask,
)
from app.db.models.hashtags.utils import extract_and_insert_hashtags
from app.db.models.tasks.task_handlers import (
    create_task,
    update_task,
    get_task_by_id,
    get_joined_task,
    delete_task,
)
from app.db.models.tasks.task_handlers import create_task, update_task, get_task_by_id
from app.db.models.grades.handlers import get_user_grades, create_grade
from app.schemas import (
    CreateTask,
    GetTaskNoForeigns,
    GetUser,
    UpdateTask,
    GetTask,
    Grade,
    GradeFeed,
    CreateGrade,
)

task_router = APIRouter(tags=["Tasks"], prefix="/tasks")


@task_router.get("/{task_id}", response_model=GetTask)
async def get_task(
    task_id: UUID4,
    current_user: GetUser = Depends(get_current_user),
) -> GetTask:
    if (task := await get_joined_task(task_id=str(task_id))) is None:
        raise TaskNotFound(str(task_id))

    if current_user.id != task.creator_id:
        # not creator, regular user
        # don't show some fields
        task.assignee = None
        task.assignee_id = None
        task.assigned_at = None
        task.due_to_date = None
        task.suggested_by_id = None
        task.suggested_by = None

    data = task.dict(exclude_unset=True)
    if data.get("due_to_date"):
        data["due_to_date"] = data["due_to_date"].isoformat()
    if data.get("assigned_at"):
        data["assigned_at"] = data["assigned_at"].isoformat()
    data["created_at"] = data["created_at"].isoformat()

    return JSONResponse(content=data)  # type: ignore


@task_router.post("", response_model=GetTaskNoForeigns, status_code=HTTPStatus.CREATED)
async def create_new_task(
    params: CreateTask,
    current_user: GetUser = Depends(get_current_user),
) -> GetTaskNoForeigns:
    if params.suggested_by_id:  # some user is suggesting a task
        # todo: check that user is subscriber of the creator
        if params.suggested_by_id != current_user.id:
            exc = "Current user id is not equal to suggested_by_id"
            raise InvalidCreatorSuggesterIds(exc=exc)
    elif params.creator_id != current_user.id:  # creator creates task for its own
        exc = "Current user id is not equal to creator_id"
        raise InvalidCreatorSuggesterIds(exc=exc)

    task, err = await create_task(params)
    if err:
        raise BadRequestCreatingTask(err)
    assert task is not None

    if task.description:
        asyncio.create_task(
            extract_and_insert_hashtags(task.description, task_id=task.id)
        )

    return task


@task_router.patch(
    path="/{task_id}",
    response_model=UpdateTask,
    response_model_exclude_unset=True,
    response_description="Dictionary with fields which were updated.",
)
async def update_task_info(
    task_id: str,
    update_task_params: UpdateTask,
    current_user: GetUser = Depends(get_current_user),
) -> UpdateTask:
    update_data: dict[str, Any] = update_task_params.dict(exclude_unset=True)

    if not (task := await get_task_by_id(task_id=task_id)):
        raise TaskNotFound(task_id=task_id)

    # if someone except creator is trying to change any fields
    if task.creator_id != current_user.id:
        raise NotCreatorPermissionError

    if (err := await update_task(task_id=task_id, values=update_data)) is not None:
        raise BadRequestUpdatingTask(exc=err)

    if (description := update_data.get("description")) is not None:
        asyncio.create_task(extract_and_insert_hashtags(description, task_id=task_id))

    # due date to string, json error otherwise
    if "due_to_date" in update_data and update_data["due_to_date"] is not None:
        update_data["due_to_date"] = update_data["due_to_date"].isoformat()

    res: JSONResponse = JSONResponse(content=update_data)
    return res  # type: ignore


@task_router.delete("/{task_id}")
async def delete_task_(
    task_id: str, current_user: GetUser = Depends(get_current_user)
) -> None:
    if not (task := await get_task_by_id(task_id=task_id)):
        raise TaskNotFound(task_id=task_id)

    # if someone except creator is trying to delete
    if task.creator_id != current_user.id:
        raise NotCreatorPermissionError

    if (err := await delete_task(task_id=task_id)) is not None:
        raise BadRequestDeletingTask(exc=err)

    return None


@task_router.get(
    path="/subscriptions",
    response_model=GradeFeed,
    response_description="A list of user subscriptions",
)
def get_subscriptions(
    current_user: GetUser = Depends(get_current_user),
) -> GradeFeed:
    res: JSONResponse = JSONResponse(
        content=get_user_grades(user_id=current_user.id, creator_id=None, task_id=None)
    )
    return res  # type: ignore


@task_router.post(
    path="/subscribe",
    response_model=Grade,
    response_description="Add grade to post or user",
)
async def add_subscription(
    params: CreateGrade,
    current_user: GetUser = Depends(get_current_user),
) -> Grade:
    # set current user id to subscription
    params.user_id = current_user.id
    res: JSONResponse = JSONResponse(content=create_grade(params))
    return res  # type: ignore
