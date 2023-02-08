from typing import Any

from app.api.auth.password_utils import passwords_are_equal
from app.api.errors import InvalidOldPassword, UserAlreadyExist
from app.db.models.users.handlers import user_exists_in_db
from app.schemas import GetUser


async def _new_username_already_exists(username: str | None) -> None:
    if username is not None and (await user_exists_in_db(username=username)):
        raise UserAlreadyExist(username)


def _old_passwords_are_equal(
    update_params: dict[str, Any], user_password: str | None
) -> None:
    """
    If both passwords (new and old one) are in update_params then:
    1. delete old_password from update params, because it can't be updated
    2. check if existing password in bd equals to old_password from request
    """
    if (
        old_password := update_params.get("old_password")
    ) is not None and update_params.get("password") is not None:
        del update_params["old_password"]
        if (old_password_in_db := user_password) is not None and not passwords_are_equal(
            old_password, old_password_in_db
        ):
            raise InvalidOldPassword


def _check_same_value_for_update(update_params: dict[str, Any], user: GetUser) -> None:
    """
    if current user's value is equal to value from request
    exclude them from update values
    """
    fields_to_delete = {
        name
        for name, value in update_params.items()
        if getattr(user, name, None) == value
    }
    for f_name in fields_to_delete:
        del update_params[f_name]


async def check_patch_params(update_params: dict[str, Any], user: GetUser) -> None:
    """
    Make some checks for update params
    Initial update_params dictionary might be changed.
    """
    await _new_username_already_exists(update_params.get("username"))
    _old_passwords_are_equal(update_params, user_password=user.password)
    _check_same_value_for_update(update_params, user=user)
