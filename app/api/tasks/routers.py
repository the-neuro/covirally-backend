import asyncio
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from app.api.auth.utils import get_current_user
from app.api.errors import (
    BadRequestCreatingTask,
    InvalidCreatorSuggesterIds,
    BadRequestUpdatingTask,
    TaskNotFound,
    NotCreatorPermissionError,
    BadRequestAddingCommentToTask,
)
from app.db.models.hashtags.utils import extract_and_insert_hashtags
from app.db.models.tasks.handlers import (
    create_task,
    update_task,
    get_task_by_id,
    add_comment_to_task,
)
from app.schemas import (
    CreateTask,
    GetTaskNoForeigns,
    GetUser,
    UpdateTask,
    GetTaskComment,
    CreateTaskComment,
)

task_router = APIRouter(tags=["Tasks"], prefix="/tasks")


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
    if "due_to_date" in update_data:
        update_data["due_to_date"] = update_data["due_to_date"].isoformat()

    res: JSONResponse = JSONResponse(content=update_data)
    return res  # type: ignore


@task_router.post(
    path="/comment",
    status_code=HTTPStatus.CREATED,
    response_model=GetTaskComment,
)
async def add_new_comment_to_task(
    params: CreateTaskComment,
    current_user: GetUser = Depends(get_current_user),
) -> GetTaskComment:
    if params.user_id != current_user.id:
        err = "Invalid user_id, not equal to current user."
        raise BadRequestAddingCommentToTask(err)

    comment, err = await add_comment_to_task(create_comment_params=params)  # type: ignore
    if err:
        raise BadRequestAddingCommentToTask(err)
    assert comment is not None
    return comment
