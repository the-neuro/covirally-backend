from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi_pagination import Page
from starlette.responses import JSONResponse

from app.api.auth.utils import get_current_user
from app.api.errors import (
    ForbiddenDeleteComment,
    CommentNotFound,
    BadRequestUpdatingComment,
    ForbiddenUpdateComment,
    BadRequestAddingCommentToTask,
)
from app.db.models.tasks.comment_handlers import (
    delete_task_comment,
    get_task_comment,
    update_task_comment,
    get_comments_for_task,
    add_comment_to_task,
)
from app.schemas import (
    GetUser,
    UpdateComment,
    CreateTaskComment,
    GetTaskComment,
    GetPaginatedTaskComment,
)


comment_router = APIRouter(tags=["Tasks comments"], prefix="/tasks")


@comment_router.get(
    path="/{task_id}/comments",
    response_model=Page[GetPaginatedTaskComment],
    response_description="Return comments with pagination",
)
async def get_paginated_comments_for_task(
    task_id: str,
    _: GetUser = Depends(get_current_user),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=10, le=20),
) -> Page[GetPaginatedTaskComment]:
    return await get_comments_for_task(task_id, page, size)


@comment_router.post(
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


@comment_router.patch(
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


@comment_router.delete(
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
