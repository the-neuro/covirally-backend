import json
import logging

from asyncpg import NotNullViolationError, UniqueViolationError
from sqlalchemy import insert, select
from databases.backends.postgres import Record
from pydantic import ValidationError

from app.db.base import database
from app.schemas import GradeFeed, CreateGrade, Grade
from app.db.models.grades.schemas import Grade as GradeSchema

logger = logging.getLogger()


async def create_grade(
    create_grade_params: CreateGrade,
) -> tuple[Grade | None, str | None]:
    """
    Allows creating grades with some limits due to grade specifics
    """
    create_params = create_grade_params.dict()

    query = insert(GradeSchema).values(create_params)
    # todo: check for payment in cases it's envolved
    transaction = await database.transaction()
    try:
        row: Record = await database.fetch_one(query)

        grade_id = row._mapping.values()
        grade: Grade = Grade.construct(**dict(id=grade_id, **create_params))
    except (NotNullViolationError, UniqueViolationError) as exc:
        logger.error(f"Can't create grade: {exc}")
        await transaction.rollback()
        return None, str(exc)
    except ValidationError as exc:
        logger.error(f"Validation error after creating grade: {exc}")
        await transaction.rollback()
        return None, str(exc)
    else:
        await transaction.commit()
        return grade, None


async def get_grade_by_id(grade_id: str) -> Grade | None:
    query = select(Grade).where(Grade.id == grade_id).limit(1)

    if not (_res := await database.fetch_one(query)):
        return None

    try:
        parsed_grade: Grade = Grade.parse_obj(_res)
    except ValidationError as exc:
        logger.error(f"Can't parse task with {grade_id=}, {_res}: {exc}")
        return None
    else:
        return parsed_grade


async def get_user_grades(user_id: str) -> GradeFeed:
    """
    Returns user grades, along with its applicability:
    0: None
    1: Subscribed
    2: Payed post
    3: Payed subscriber
    4: Team creator
    5: Is creator
    """
    query = """
    SELECT ALL
        AS grades
    FROM grades WHERE user_id=:user_id;
    """
    fetched_data = await database.fetch_one(query, values={"user_id": user_id})
    res: GradeFeed = GradeFeed.parse_obj({"grades": json.loads(fetched_data["grades"])})
    return res
