from datetime import datetime, timedelta
from http import HTTPStatus

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError

from app.api.auth.types import DataToEncodeInJWTToken
from app.api.errors import (
    UserNotFound,
    InvalidAccessToken,
    InvalidAccessTokenPayload,
    AccessTokenExpired,
)
from app.api.auth.password_utils import (
    passwords_are_equal,
    password_needs_rehash,
    get_password_hash,
)

from app.config import settings
from app.db.models.users.handlers import get_user_by_username, get_user, update_user
from app.schemas import GetUser

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def authenticate_user(username: str, password: str) -> GetUser | None:
    if not (user := await get_user_by_username(username)):
        return None
    if not user.password:
        return None
    if not passwords_are_equal(password, user.password):
        return None
    return user


def create_access_token(
    user_id: str, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES
) -> str:
    encode_data = DataToEncodeInJWTToken(
        user_id=user_id,
        exp=datetime.utcnow() + timedelta(minutes=expires_minutes),
    )

    token: str = jwt.encode(encode_data, settings.secret_jwt_token, algorithm=ALGORITHM)
    return token


async def get_current_user(token: str = Depends(oauth2_scheme)) -> GetUser:
    try:
        payload: DataToEncodeInJWTToken = jwt.decode(
            token, settings.secret_jwt_token, algorithms=[ALGORITHM]
        )
        if (user_id := payload.get("user_id")) is None:
            raise InvalidAccessTokenPayload
    except ExpiredSignatureError as exc:
        raise AccessTokenExpired from exc
    except JWTError as exc:
        raise InvalidAccessToken from exc

    if (user := await get_user(user_id=user_id)) is None:
        raise UserNotFound(user_param=user_id, status_code=HTTPStatus.UNAUTHORIZED)

    if user.password is not None and password_needs_rehash(user.password):
        new_password = get_password_hash(user.password)
        await update_user(user_id=user_id, values={"password": new_password})
    return user
