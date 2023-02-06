from pydantic import BaseModel

from app.api.auth.types import AccessTokenType


class GetBearerAccessTokenResponse(BaseModel):
    access_token: str
    token_type: AccessTokenType
