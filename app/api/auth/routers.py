from datetime import datetime, timezone
from http import HTTPStatus

from fastapi import APIRouter, Depends
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
    OAuth2PasswordEmailRequestForm,
)
from app.api.auth.verify_email import (
    get_user_from_verify_email_token,
    create_verify_token_and_send_to_email,
)
from app.api.errors import InvalidAuthorization, UserNotFound, EmailIsAlreadyVerified
from app.api.auth.schemas import (
    GetBearerAccessTokenResponse,
    ResendVerifyEmail,
    RefreshPasswordForEmail,
    RefreshPassword,
)
from app.db.models.users.handlers import update_user, get_user_by_email

auth_router = APIRouter(tags=["Authentication"], prefix="/auth")


@auth_router.post("/token", response_model=GetBearerAccessTokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordEmailRequestForm = Depends(),
) -> GetBearerAccessTokenResponse:
    """
    This endpoint authorizes user
    :returns bearer for future requests.
    """
    user, err = await authenticate_user(
        email=form_data.email, password=form_data.password
    )
    if err:
        raise InvalidAuthorization(err)

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
        redirect_url = "https://covirally.com"
    else:
        redirect_url = "https://covirally.com/pricing"
        update_data = {
            "email_is_verified": True,
            "email_verified_at": datetime.now(timezone.utc),
        }
        await update_user(user_id=user.id, values=update_data)
    return RedirectResponse(url=redirect_url)


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
