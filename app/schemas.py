import json
from datetime import datetime, timezone
from typing import Any

import pytz  # type: ignore
from pydantic import BaseModel, validator, Field, root_validator

from app.api.auth.password_utils import get_password_hash
from app.types import TaskStatus, EMAIL_REGEX

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
        default=None, max_length=35, regex=EMAIL_REGEX, example="random@gmail.com"
    )

    receive_email_alerts: bool | None = Field(default=None)


class CreateUser(_BaseUser):
    """
    username and password are mondatory
    """

    password: str = Field(min_length=8, max_length=256)

    email: str = Field(max_length=35, regex=EMAIL_REGEX, example="random@gmail.com")

    receive_email_alerts: bool = True

    @root_validator(pre=True)
    def check_cant_create_with_system_fields(  # pylint: disable=no-self-argument
        cls, values: dict[str, Any]
    ) -> dict[str, Any]:
        system_fields = ("id", "created_at", "email_is_verified", "email_verified_at")

        system_fields_in_request = [field for field in system_fields if field in values]
        err = f"Can't create with following fields: {system_fields_in_request}"
        assert not system_fields_in_request, err
        return values

    @validator("password")
    def hash_password(cls, password: str) -> str:  # pylint: disable=no-self-argument
        return get_password_hash(password)

    @root_validator()
    def explicitly_set_to_default_values(  # pylint: disable=no-self-argument
        cls, values: dict[str, Any]
    ) -> dict[str, Any]:
        values["email_is_verified"] = False
        values["email_verified_at"] = None
        return values


class GetUser(_BaseUser):
    id: str  # noqa

    email: str = Field(max_length=35, regex=EMAIL_REGEX, example="random@gmail.com")
    receive_email_alerts: bool
    email_is_verified: bool
    email_verified_at: datetime | None

    created_at: datetime


class UpdateUser(_BaseUser):
    old_password: str | None = Field(default=None, min_length=1, max_length=256)

    email_is_verified: bool | None = Field(default=None)
    email_verified_at: datetime | None = Field(default=None)

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
        system_fields = ("id", "created_at", "email_is_verified", "email_verified_at")

        system_fields_in_request = [field for field in system_fields if field in values]
        err = f"Following fields can't be updated: {system_fields_in_request}"
        assert not system_fields_in_request, err
        return values


class _BaseTask(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=128)
    description: str | None = Field(default=None, min_length=1, max_length=1024)
    due_to_date: datetime | None = Field(
        default=None, description="Date when task must be done"
    )

    status: TaskStatus | None = Field(default=TaskStatus.IDEA)

    creator_id: str | None = Field(default=None, min_length=36, max_length=36)
    suggested_by_id: str | None = Field(default=None, min_length=36, max_length=36)

    assignee_id: str | None = Field(default=None, min_length=36, max_length=36)


class CreateTask(_BaseTask):
    title: str = Field(min_length=2, max_length=128)
    creator_id: str = Field()
    status: TaskStatus = Field(default=TaskStatus.IDEA)

    @validator("due_to_date")
    def check_date_in_future(  # pylint: disable=no-self-argument  # noqa
        cls, due_to_date: datetime | None
    ) -> datetime | None:
        if not due_to_date:
            return None

        if not due_to_date.replace(tzinfo=pytz.UTC) > datetime.now(timezone.utc):
            raise ValueError("due_to_date must be date in future")
        return due_to_date

    @root_validator()
    def set_assigned_at_if_neccessary(  # pylint: disable=no-self-argument
        cls, values: dict[str, Any]
    ) -> dict[str, Any]:
        if (values.get("assignee_id")) is not None and values.get("assigned_at") is None:
            values["assigned_at"] = datetime.now(tz=timezone.utc)
        return values


class UpdateTask(_BaseTask):
    @validator("due_to_date")
    def check_date_in_future(  # pylint: disable=no-self-argument  # noqa
        cls, due_to_date: datetime | None
    ) -> datetime | None:
        if not due_to_date:
            return None

        if not due_to_date.replace(tzinfo=pytz.UTC) > datetime.now(timezone.utc):
            raise ValueError("due_to_date must be date in future")
        return due_to_date

    @root_validator()
    def set_assigned_at_if_neccessary(  # pylint: disable=no-self-argument
        cls, values: dict[str, Any]
    ) -> dict[str, Any]:
        if (values.get("assignee_id")) is not None and values.get("assigned_at") is None:
            values["assigned_at"] = datetime.now(tz=timezone.utc)
        return values

    @root_validator(pre=True)
    def check_cant_patch_system_fields(  # pylint: disable=no-self-argument
        cls, values: dict[str, Any]
    ) -> dict[str, Any]:
        system_fields = (
            "id",
            "created_at",
            "assigned_at",
            "creator_id",
            "suggested_by_id",
        )

        system_fields_in_request = [field for field in system_fields if field in values]
        err = f"Following fields can't be updated: {system_fields_in_request}"
        assert not system_fields_in_request, err
        return values


class GetTaskNoForeigns(_BaseTask):
    """
    Don't return joined DB fields like creator, assignee or suggested_by
    Return only ids of those instead.
    """

    id: str  # noqa

    title: str

    creator_id: str

    assigned_at: datetime | None
    created_at: datetime


class UserTask(BaseModel):
    id: str  # noqa
    username: str | None
    avatar_url: str | None


class GetTask(_BaseTask):
    id: str  # noqa

    title: str

    creator: UserTask

    assignee: UserTask | None = None
    assigned_at: datetime | None = None

    suggested_by: UserTask | None = None

    created_at: datetime

    @validator("creator", pre=True)
    def load_creator(cls, value: str) -> UserTask:  # pylint: disable=no-self-argument
        res: UserTask = UserTask.construct(**json.loads(value))
        return res

    @validator("assignee", pre=True)
    def load_assignee(  # pylint: disable=no-self-argument
        cls, value: str | None
    ) -> UserTask | None:
        if value:
            res: UserTask | None = UserTask.construct(**json.loads(value))
        else:
            res = None
        return res

    @validator("suggested_by", pre=True)
    def load_suggested_by(  # pylint: disable=no-self-argument
        cls, value: str | None
    ) -> UserTask | None:
        if value:
            res: UserTask | None = UserTask.construct(**json.loads(value))
        else:
            res = None
        return res


class HashTag(BaseModel):
    id: str  # noqa
    hashtag: str


class TaskHashtags(BaseModel):
    hashtags: list[HashTag]


class CreateTaskComment(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

    task_id: str
    user_id: str

    @validator("content", pre=True)
    def strip_content(cls, value: str) -> str:  # pylint: disable=no-self-argument
        return value.strip()


class GetTaskComment(BaseModel):
    id: str  # noqa

    content: str

    task_id: str
    user_id: str

    edited: bool
    edited_at: datetime | None

    created_at: datetime


class UpdateComment(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=2000)

    @validator("content", pre=True)
    def strip_content(cls, value: str) -> str:  # pylint: disable=no-self-argument
        return value.strip()

    @root_validator(pre=True)
    def check_cant_patch_system_fields(  # pylint: disable=no-self-argument
        cls, values: dict[str, Any]
    ) -> dict[str, Any]:
        system_fields = (
            "id",
            "task_id",
            "user_id",
            "edited",
            "edited_at",
            "created_at",
        )

        system_fields_in_request = [field for field in system_fields if field in values]
        err = f"Following fields can't be updated: {system_fields_in_request}"
        assert not system_fields_in_request, err
        return values


class UserFeed(BaseModel):
    id: str  # noqa
    username: str
    avatar_url: str | None


class TaskFeed(BaseModel):
    id: str  # noqa
    title: str
    description: str | None = None
    created_at: str
    status: TaskStatus
    creator: UserFeed


class TasksFeed(BaseModel):
    tasks: list[TaskFeed]
