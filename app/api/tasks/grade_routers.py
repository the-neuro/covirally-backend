from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from app.api.auth.utils import get_current_user
from app.schemas import (
    GetUser,
    CreateGrade,
    GradeFeed,
)
from app.db.models.grades.handlers import (
    create_grade,
    get_user_grades,
)

grade_router = APIRouter(tags=["Grades"], prefix="/tasks")


@grade_router.get(
    path="/subscriptions",
    response_model=GradeFeed,
    response_description="A list of user subscriptions",
)
def get_subscriptions(
    current_user: GetUser = Depends(get_current_user),
) -> GradeFeed:
    res: JSONResponse = JSONResponse(content=get_user_grades(user_id=current_user.id))
    return res  # type: ignore


@grade_router.post(
    path="/subscribe",
    response_description="Add grade to post or user",
)
async def add_subscription(
    params: CreateGrade,
    current_user: GetUser = Depends(get_current_user),
) -> None:
    # set current user id to subscription
    params.user_id = current_user.id
    await create_grade(params)
    return None
