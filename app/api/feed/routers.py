from fastapi import APIRouter, Depends

from app.api.auth.utils import get_curr_user_or_none
from app.db.models.tasks.handlers import get_feed_tasks
from app.schemas import GetUser, TasksFeed

feed_router = APIRouter(tags=["Task's feed"], prefix="/feed")


@feed_router.get(
    "",
    description="""
    Authorization for this endpoint is optional.
    If 'Authorization' header is provided, then backend tries to authenticate a user,
    hence, there are might be some auth errors.
    If 'Authorization' header is not provided, then authentication is not occured.
    """,
    response_model=TasksFeed,
)
async def get_task_feed_for_user(
    current_user: GetUser  # pylint: disable=unused-argument
    | None = Depends(get_curr_user_or_none),
) -> TasksFeed:
    # todo: add personalization for user
    return await get_feed_tasks()
