from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from app.api.auth.utils import get_current_user
from app.api.errors import (
    UserAlreadyExist,
    BadRequestCreatingUser,
    BadRequestUpdatingUser,
)
from app.api.users.patch_user_utils import check_patch_params
from app.db.models.users.handlers import (
    create_user,
    get_user_by_username,
    update_user,
)
from app.schemas import GetUser, CreateUser, UpdateUser

users_router = APIRouter(tags=["Users"], prefix="/users")


@users_router.post("", response_model=GetUser)
async def create_new_user(user_params: CreateUser) -> JSONResponse:
    """
    Creating new user
    Checking if user is already exists with such username
    """
    username = user_params.username
    if await get_user_by_username(username) is not None:
        raise UserAlreadyExist(username)

    res, err = await create_user(create_user_params=user_params)
    if err:
        raise BadRequestCreatingUser(exc=err)
    assert res is not None

    return JSONResponse(content=res.json(), status_code=HTTPStatus.CREATED)


@users_router.get("/me", response_model=GetUser)
async def get_user_info_for_logged_user(
    current_user: GetUser = Depends(get_current_user),
) -> GetUser:
    """
    Get data for authorized user
    """
    return current_user


@users_router.patch(
    "",
    response_model=UpdateUser,
    response_model_exclude_unset=True,
    response_description="Dictionary with fields which were updated.",
)
async def update_user_info(
    update_user_params: UpdateUser,
    curr_user: GetUser = Depends(get_current_user),
) -> UpdateUser:
    update_data: dict[str, Any] = update_user_params.dict(exclude_unset=True)

    await check_patch_params(update_params=update_data, user=curr_user)

    if (err := await update_user(user_id=curr_user.id, values=update_data)) is not None:
        raise BadRequestUpdatingUser(exc=err)

    res: JSONResponse = JSONResponse(content=update_data)
    return res  # type: ignore
