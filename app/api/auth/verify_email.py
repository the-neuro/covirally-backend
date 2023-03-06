import asyncio
from http import HTTPStatus

from jose import jwt, JWTError

from app.api.auth.types import VerificationEmailData
from app.api.auth.utils import ALGORITHM
from app.api.errors import InvalidVerifyEmailToken, UserNotFound
from app.config import settings
from app.db.models.users.handlers import get_user_by_email
from app.email.mailgun import mailgun
from app.schemas import GetUser


async def get_user_from_verify_email_token(verify_token: str) -> GetUser:
    try:
        payload: VerificationEmailData = jwt.decode(
            verify_token, settings.secret_jwt_token, algorithms=[ALGORITHM]
        )
    except JWTError as exc:
        raise InvalidVerifyEmailToken from exc

    if (email := payload.get("email")) is None:
        raise InvalidVerifyEmailToken

    if not (user := await get_user_by_email(email)):
        raise UserNotFound(email, status_code=HTTPStatus.UNAUTHORIZED)
    return user


def create_verify_email_token(email: str) -> str:
    data = VerificationEmailData(email=email)
    token: str = jwt.encode(data, settings.secret_jwt_token, algorithm=ALGORITHM)
    return token


def create_verify_token_and_send_to_email(email: str) -> None:
    verify_token = create_verify_email_token(email=email)
    asyncio.create_task(
        mailgun.send_email_confirmation(verfiy_email_token=verify_token, to_address=email)
    )
