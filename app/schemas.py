from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    id: str  # noqa

    first_name: str
    last_name: str

    username: str | None
    password: str | None
    avatar_url: str | None

    email: str
    telephone_number: str | None

    receive_email_alerts: bool

    created_at: datetime
