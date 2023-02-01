import logging

from pydantic import ValidationError
from sqlalchemy import select

from app.db.base import database
from app.db.models.users.schemas import User as UserTable
from app.schemas import User

logger = logging.getLogger()


async def get_user(user_id: str) -> User | None:
    query = select(UserTable).where(UserTable.id == user_id).limit(1)

    if not (_res := await database.fetch_one(query)):
        logger.info(f"Can't get user with {user_id=} from db.")
        return None

    try:
        parsed_user: User = User.parse_obj(_res)
    except ValidationError as exc:
        logger.error(f"Can't parse user by {user_id=}, {_res}: {exc}")
        return None
    else:
        return parsed_user


async def get_user_by_username(username: str) -> User | None:
    query = select(UserTable).where(UserTable.username == username).limit(1)

    if not (_res := await database.fetch_one(query)):
        logger.info(f"No user with {username=} in db.")
        return None

    try:
        parsed_user: User = User.parse_obj(_res)
    except ValidationError as exc:
        logger.error(f"Can't parse user by {username=}, {_res}: {exc}")
        return None
    else:
        return parsed_user
