from app.api.auth.password_utils import get_password_hash, passwords_are_equal

PASSWORD = "hello_world"


def test_password_is_defferent_after_hashing():

    # hashed password doesn't equal to initial one
    hashed_password_1 = get_password_hash(PASSWORD)
    assert PASSWORD != hashed_password_1

    # after hashing same password, hashes are different
    hashed_password_2 = get_password_hash(PASSWORD)
    assert PASSWORD != hashed_password_2
    assert hashed_password_1 != hashed_password_2


def test_passwords_are_equal():
    hashed_password = get_password_hash(PASSWORD)
    assert passwords_are_equal(PASSWORD, hashed_password)
