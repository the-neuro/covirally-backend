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
    BadRequestAddingCommentToTask,
    ForbiddenUpdateComment,
    CommentNotFound,
    BadRequestUpdatingComment,
    ForbiddenDeleteComment,
)
from app.db.models.hashtags.utils import extract_and_insert_hashtags
from app.db.models.tasks.handlers import (
    create_task,
    update_task,
    get_task_by_id,
    add_comment_to_task,
    get_task_comment,
    update_task_comment,
    delete_task_comment,
    get_joined_task,
)
from app.schemas import (
    CreateTask,
    GetTaskNoForeigns,
    GetUser,
    UpdateTask,
    GetTaskComment,
    CreateTaskComment,
    UpdateComment,
    GetTask,
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


@task_router.patch(
    path="/comment/{comment_id}",
    response_model=UpdateComment,
    response_model_exclude_unset=True,
    response_description="Dictionary with fields which were updated.",
)
async def update_comment(
    comment_id: str,
    update_params: UpdateComment,
    current_user: GetUser = Depends(get_current_user),
) -> UpdateComment:
    update_data: dict[str, Any] = update_params.dict(exclude_unset=True)

    if (comment := await get_task_comment(comment_id=comment_id)) is None:
        raise CommentNotFound(comment_id=comment_id)

    if comment.user_id != current_user.id:
        raise ForbiddenUpdateComment

    if (err := await update_task_comment(comment_id, values=update_data)) is not None:
        raise BadRequestUpdatingComment(exc=err)

    res: JSONResponse = JSONResponse(content=update_data)
    return res  # type: ignore


@task_router.delete(
    path="/comment/{comment_id}",
    response_description="Success response is null with 200 status code.",
)
async def remove_task_comment(
    comment_id: str,
    current_user: GetUser = Depends(get_current_user),
) -> None:

    if (comment := await get_task_comment(comment_id=comment_id)) is None:
        raise CommentNotFound(comment_id=comment_id)

    if comment.user_id != current_user.id:
        raise ForbiddenDeleteComment

    await delete_task_comment(comment_id)
