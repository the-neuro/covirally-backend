from datetime import datetime
from typing import Any

from pydantic import BaseModel, validator, Field, root_validator

from app.api.auth.password_utils import get_password_hash

EMAIL_REGEX = r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"
URL_REGEX = r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"  # noqa


class _BaseUser(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=64)
    last_name: str | None = Field(default=None, min_length=1, max_length=64)

    username: str | None = Field(default=None, min_length=2, max_length=64)
    password: str | None = Field(default=None, min_length=8, max_length=256)

    avatar_url: str | None = Field(
        default=None, regex=URL_REGEX, example="https://google.com/some_picture.jpg"
    )

    email: str | None = Field(
        default=None, max_length=128, regex=EMAIL_REGEX, example="random@gmail.com"
    )
    telephone_number: str | None = Field(default=None, regex=r"^\+\d{11}$")

    receive_email_alerts: bool | None = Field(default=None)


class CreateUser(_BaseUser):
    """
    username and password are mondatory
    """

    first_name: str = Field(min_length=1, max_length=64)
    last_name: str = Field(min_length=1, max_length=64)

    password: str = Field(min_length=8, max_length=256)

    email: str = Field(max_length=128, regex=EMAIL_REGEX, example="random@gmail.com")

    receive_email_alerts: bool = True

    @validator("password")
    def hash_password(cls, password: str) -> str:  # pylint: disable=no-self-argument
        return get_password_hash(password)


class GetUser(_BaseUser):
    id: str  # noqa

    first_name: str = Field(min_length=1, max_length=64)
    last_name: str = Field(min_length=1, max_length=64)

    email: str = Field(max_length=128, regex=EMAIL_REGEX, example="random@gmail.com")
    receive_email_alerts: bool

    created_at: datetime


class UpdateUser(_BaseUser):
    old_password: str | None = Field(default=None, min_length=1, max_length=256)

    @validator("password")
    def hash_new_password(  # pylint: disable=no-self-argument
        cls, password: str | None
    ) -> str | None:
        return get_password_hash(password) if password is not None else password

    @root_validator
    def check_presense_of_passwords(  # pylint: disable=no-self-argument
        cls, values: dict[str, Any]
    ) -> dict[str, Any]:
        old_password: str | None = values.get("old_password")
        new_password: str | None = values.get("password")

        # both passwords are present
        if old_password is not None:
            assert new_password is not None, "New password is required to change password"
        # or both passwords are not present
        else:
            assert new_password is None, "Old password is required to change password"
        return values

    @root_validator(pre=True)
    def check_different_passwords(  # pylint: disable=no-self-argument
        cls, values: dict[str, Any]
    ) -> dict[str, Any]:
        """
        new password and old passwrod must be different
        """
        if (old_password := values.get("old_password")) is not None and (
            new_password := values.get("password")
        ) is not None:
            assert (
                old_password != new_password
            ), "New password must be different from existing one."

        return values

    @root_validator(pre=True)
    def check_cant_patch_system_fields(  # pylint: disable=no-self-argument
        cls, values: dict[str, Any]
    ) -> dict[str, Any]:
        system_fields = ("id", "created_at")

        system_fields_in_request = [field for field in system_fields if field in values]
        err = f"Following fields can't be updated: {system_fields_in_request}"
        assert not system_fields_in_request, err
        return values
