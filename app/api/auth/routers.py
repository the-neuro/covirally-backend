from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.auth.types import AccessTokenType
from app.api.auth.utils import (
    authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
)
from app.api.errors import InvalidCredentials
from app.api.auth.schemas import GetBearerAccessTokenResponse


auth_router = APIRouter(tags=["Authentication"], prefix="/auth")


@auth_router.post("/token", response_model=GetBearerAccessTokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> GetBearerAccessTokenResponse:
    """
    This endpoint authorizes user
    :returns bearer for future requests.
    """
    if not (user := await authenticate_user(form_data.username, form_data.password)):
        raise InvalidCredentials()
    access_token = create_access_token(
        user_id=user.id, expires_minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    res: GetBearerAccessTokenResponse = GetBearerAccessTokenResponse(
        access_token=access_token,
        token_type=AccessTokenType.BEARER,
    )
    return res
