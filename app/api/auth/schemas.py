from pydantic import BaseModel, Field, validator

from app.api.auth.password_utils import get_password_hash
from app.api.auth.types import AccessTokenType
from app.types import EMAIL_REGEX


class GetBearerAccessTokenResponse(BaseModel):
    access_token: str
    token_type: AccessTokenType


class ResendVerifyEmail(BaseModel):
    email: str = Field(
        min_length=3, max_length=35, regex=EMAIL_REGEX, example="email@gmail.com"
    )


class RefreshPasswordForEmail(BaseModel):
    email: str = Field(
        min_length=3, max_length=35, regex=EMAIL_REGEX, example="email@gmail.com"
    )


class RefreshPassword(BaseModel):
    password: str = Field(min_length=8, max_length=64)

    @validator("password")
    def hash_password(cls, password: str) -> str:  # pylint: disable=no-self-argument
        return get_password_hash(password)
