from datetime import datetime, timedelta
from http import HTTPStatus

from fastapi import Depends
from fastapi.param_functions import Form
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError

from app.api.auth.types import DataToEncodeInJWTToken
from app.api.errors import (
    UserNotFound,
    InvalidAccessToken,
    InvalidAccessTokenPayload,
    AccessTokenExpired,
    InvalidAuthorization,
)
from app.api.auth.password_utils import (
    passwords_are_equal,
    password_needs_rehash,
    get_password_hash,
)

from app.config import settings
from app.db.models.users.handlers import update_user, get_user_by_email
from app.schemas import GetUser
from app.types import EMAIL_REGEX

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


class OAuth2PasswordEmailRequestForm:
    """
    This is a dependency class, use it like:

        @app.post("/login")
        def login(form_data: OAuth2PasswordEmailRequestForm = Depends()):
            data = form_data.parse()
            print(data.email)
            print(data.password)
            for scope in data.scopes:
                print(scope)
            if data.client_id:
                print(data.client_id)
            if data.client_secret:
                print(data.client_secret)
            return data


    It creates the following Form request parameters in your endpoint:

    grant_type: OAuth2 spec says it is required and MUST be the fixed string "password".
    email: email string.
    password: password string. The OAuth2 spec requires the exact field name "password".
    scope: Optional string. Several scopes (each one a string) separated by spaces. E.g.
        "items:read items:write users:read profile openid"
    client_id: optional string. OAuth2 recommends sending the client_id and client_secret
        using HTTP Basic auth, as: client_id:client_secret
    client_secret: optional string. -- recommends sending the client_id and client_secret
        using HTTP Basic auth, as: client_id:client_secret
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        grant_type: str = Form(default=None, regex="password"),
        email: str = Form(regex=EMAIL_REGEX),
        password: str = Form(),
        scope: str = Form(default=""),
        client_id: str | None = Form(default=None),
        client_secret: str | None = Form(default=None),
    ):
        self.grant_type = grant_type
        self.email = email
        self.password = password
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret


async def authenticate_user(
    email: str, password: str
) -> tuple[GetUser | None, Exception | None]:
    if not (user := await get_user_by_email(email)):
        return None, UserNotFound(email)

    # todo: don't do this check when user is registered via google, twitter, FB, etc
    if not user.email_is_verified:
        return None, InvalidAuthorization(f"Email {email} is not verified.")

    if user.password and not passwords_are_equal(password, user.password):
        return None, InvalidAuthorization("Invlaid password")
    return user, None


def create_access_token(
    email: str, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES
) -> str:
    encode_data = DataToEncodeInJWTToken(
        email=email,
        exp=datetime.utcnow() + timedelta(minutes=expires_minutes),
    )

    token: str = jwt.encode(encode_data, settings.secret_jwt_token, algorithm=ALGORITHM)
    return token


async def _get_curr_user(token: str | None) -> GetUser | None:
    if not token:
        return None

    try:
        payload: DataToEncodeInJWTToken = jwt.decode(
            token, settings.secret_jwt_token, algorithms=[ALGORITHM]
        )
        if (email := payload.get("email")) is None:
            raise InvalidAccessTokenPayload
    except ExpiredSignatureError as exc:
        raise AccessTokenExpired from exc
    except JWTError as exc:
        raise InvalidAccessToken from exc

    if (user := await get_user_by_email(email=email)) is None:
        raise UserNotFound(user_param=email, status_code=HTTPStatus.UNAUTHORIZED)

    if user.password is not None and password_needs_rehash(user.password):
        new_password = get_password_hash(user.password)
        await update_user(user_id=user.id, values={"password": new_password})
    return user


async def get_curr_user_or_none(
    token: str | None = Depends(optional_oauth2_scheme),
) -> GetUser | None:
    return await _get_curr_user(token)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> GetUser:
    user = await _get_curr_user(token)
    assert user is not None
    return user
