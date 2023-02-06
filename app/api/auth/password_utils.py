from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher()


def get_password_hash(password: str) -> str:
    """
    password: human-readable user's password
    return: hash of password which will be stored in db
    """
    hashed_password: str = _ph.hash(password)
    return hashed_password


def passwords_are_equal(password: str, hashed_password: str) -> bool:
    try:
        _ph.verify(hashed_password, password)
    except VerifyMismatchError:
        return False
    else:
        return True


def password_needs_rehash(hashed_password: str) -> bool:
    res: bool = _ph.check_needs_rehash(hashed_password)
    return res
