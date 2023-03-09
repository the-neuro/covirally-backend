from datetime import datetime, timezone
from http import HTTPStatus

from fastapi import APIRouter, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import RedirectResponse

from app.api.auth.refresh_password import (
    create_refresh_password_token_and_send,
    get_user_from_refresh_password_token,
)
from app.api.auth.types import AccessTokenType
from app.api.auth.utils import (
    authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
)
from app.api.auth.verify_email import (
    get_user_from_verify_email_token,
    create_verify_token_and_send_to_email,
)
from app.api.errors import UserNotFound, EmailIsAlreadyVerified
from app.api.auth.schemas import (
    GetBearerAccessTokenResponse,
    ResendVerifyEmail,
    RefreshPasswordForEmail,
    RefreshPassword,
)
from app.config import settings
from app.db.models.users.handlers import update_user, get_user_by_email
from app.types import EMAIL_REGEX

auth_router = APIRouter(tags=["Authentication"], prefix="/auth")


@auth_router.post("/token", response_model=GetBearerAccessTokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> GetBearerAccessTokenResponse:
    """
    This endpoint authorizes user
    :returns bearer for future requests.
    """
    user, err = await authenticate_user(
        email=form_data.username, password=form_data.password
    )
    if err:
        raise err

    assert user is not None
    access_token = create_access_token(
        email=user.email, expires_minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    res: GetBearerAccessTokenResponse = GetBearerAccessTokenResponse(
        access_token=access_token,
        token_type=AccessTokenType.BEARER,
    )
    return res


@auth_router.get("/verifyemail/{token}", status_code=HTTPStatus.PERMANENT_REDIRECT)
async def verify_email_via_jwt_token(token: str) -> RedirectResponse:
    user = await get_user_from_verify_email_token(verify_token=token)

    # todo: change this url for both cases
    if user.email_is_verified:
        redirect_url = f"https://{settings.frontend_host}"
    else:
        redirect_url = f"https://{settings.frontend_host}/pricing"
        update_data = {
            "email_is_verified": True,
            "email_verified_at": datetime.now(timezone.utc),
        }
        await update_user(user_id=user.id, values=update_data)

    return RedirectResponse(url=redirect_url, status_code=HTTPStatus.PERMANENT_REDIRECT)


@auth_router.post("/verifyemail/resend")
async def resend_verification_email(params: ResendVerifyEmail) -> None:
    if not (user := await get_user_by_email(email=params.email)):
        raise UserNotFound(params.email)

    if user.email_is_verified:
        raise EmailIsAlreadyVerified(user.email)

    create_verify_token_and_send_to_email(email=user.email)


@auth_router.post("/refresh-password/")
async def send_refresh_password_email(params: RefreshPasswordForEmail) -> None:
    if not (user := await get_user_by_email(email=params.email)):
        raise UserNotFound(params.email)

    create_refresh_password_token_and_send(email=user.email)


@auth_router.post("/refresh-password/{token}")
async def change_password_via_token(
    token: str,
    params: RefreshPassword,
) -> None:
    user = await get_user_from_refresh_password_token(token)
    await update_user(user_id=user.id, values={"password": params.password})


@auth_router.get("/check-email", status_code=HTTPStatus.PERMANENT_REDIRECT)
async def check_if_user_exists(
    email: str = Query(
        ..., min_length=3, max_length=35, regex=EMAIL_REGEX, example="email@gmail.com"
    ),
) -> RedirectResponse:
    # todo: change these redirect urls
    if await get_user_by_email(email):
        redirect_url = f"https://{settings.frontend_host}/auth"  # authorization
    else:
        redirect_url = f"https://{settings.frontend_host}/registration"  # registration
    return RedirectResponse(url=redirect_url, status_code=HTTPStatus.PERMANENT_REDIRECT)
