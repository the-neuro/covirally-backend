from http import HTTPStatus

from fastapi import APIRouter, Depends

from app.api.auth.utils import get_current_user
from app.api.errors import BadRequestCreatingTask, InvalidCreatorSuggesterIds
from app.db.models.tasks.handlers import create_task
from app.schemas import CreateTask, GetTaskNoForeigns, GetUser

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

    return task
