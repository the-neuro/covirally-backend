from datetime import datetime
from enum import Enum
from typing import TypedDict


class AccessTokenType(str, Enum):
    BEARER = "Bearer"


class DataToEncodeInJWTToken(TypedDict):
    email: str
    exp: datetime
