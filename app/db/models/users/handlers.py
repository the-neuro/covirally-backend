import logging
from typing import Any

from databases.backends.postgres import Record
from pydantic import ValidationError
from sqlalchemy import select, insert, literal_column, update

from app.db.base import database
from app.db.models.users.schemas import User
from app.schemas import GetUser, CreateUser

logger = logging.getLogger()


async def get_user(user_id: str) -> GetUser | None:
    query = select(User).where(User.id == user_id).limit(1)

    if not (_res := await database.fetch_one(query)):
        logger.info(f"Can't get user with {user_id=} from db.")
        return None

    try:
        parsed_user: GetUser = GetUser.parse_obj(_res)
    except ValidationError as exc:
        logger.error(f"Can't parse user by {user_id=}, {_res}: {exc}")
        return None
    else:
        return parsed_user


async def get_user_by_username(username: str) -> GetUser | None:
    query = select(User).where(User.username == username).limit(1)

    if not (_res := await database.fetch_one(query)):
        return None

    try:
        parsed_user: GetUser = GetUser.parse_obj(_res)
    except ValidationError as exc:
        logger.error(f"Can't parse user by {username=}, {_res}: {exc}")
        return None
    else:
        return parsed_user


async def create_user(create_user_params: CreateUser) -> GetUser:
    create_params = create_user_params.dict()

    query = (
        insert(User)
        .values(**create_params)
        .returning(literal_column("id"), literal_column("created_at"))
    )
    row: Record = await database.fetch_one(query)
    user_id, created_at = row._mapping.values()

    user: GetUser = GetUser.construct(
        **dict(id=user_id, created_at=created_at, **create_params)
    )
    return user


async def user_exists_in_db(username: str) -> bool:
    query = select([User.id]).where(User.username == username).limit(1)
    res: Record = await database.fetch_one(query)
    return bool(res)


async def update_user(user_id: str, values: dict[str, Any]) -> None:
    if values == {}:
        return None

    query = update(User).where(User.id == user_id).values(values)
    await database.execute(query)
