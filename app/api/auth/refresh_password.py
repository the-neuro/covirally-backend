import asyncio
from datetime import datetime, timezone, timedelta
from http import HTTPStatus

from jose import jwt, JWTError, ExpiredSignatureError

from app.api.auth.types import RefreshPasswordData
from app.api.auth.utils import ALGORITHM
from app.api.errors import (
    RefreshPasswordTokenIsExpired,
    InvalidRefreshPasswordToken,
    UserNotFound,
)
from app.config import settings
from app.db.models.users.handlers import get_user_by_email
from app.email.mailgun import mailgun
from app.schemas import GetUser


REFRESH_PASSWORD_EXPIRES_HOURS = 2


def create_refresh_password_token(
    email: str, expires_hours: int = REFRESH_PASSWORD_EXPIRES_HOURS
) -> str:
    data = RefreshPasswordData(
        email=email,
        exp=datetime.now(timezone.utc) + timedelta(hours=expires_hours),
    )
    token: str = jwt.encode(data, settings.secret_jwt_token, algorithm=ALGORITHM)
    return token


def create_refresh_password_token_and_send(email: str) -> None:
    refresh_password_token = create_refresh_password_token(email=email)
    asyncio.create_task(
        mailgun.send_refresh_password(
            refresh_password_token=refresh_password_token, to_address=email
        )
    )


async def get_user_from_refresh_password_token(token: str) -> GetUser:
    try:
        payload: RefreshPasswordData = jwt.decode(
            token, settings.secret_jwt_token, algorithms=[ALGORITHM]
        )
    except ExpiredSignatureError as exc:
        raise RefreshPasswordTokenIsExpired from exc
    except JWTError as exc:
        raise InvalidRefreshPasswordToken from exc

    if (email := payload.get("email")) is None:
        raise InvalidRefreshPasswordToken

    if not (user := await get_user_by_email(email)):
        raise UserNotFound(email, status_code=HTTPStatus.BAD_REQUEST)
    return user
