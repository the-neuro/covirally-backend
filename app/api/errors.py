from http import HTTPStatus

from fastapi import HTTPException


class InvalidCredentials(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Invalid credentials for authorization",
        )


class InvalidAccessToken(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid access token"
        )


class AccessTokenExpired(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Access token is expired"
        )


class InvalidAccessTokenPayload(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Access token is missing required params",
        )


class UserNotFound(HTTPException):
    def __init__(self, user_param: str, status_code: int = HTTPStatus.NOT_FOUND) -> None:
        super().__init__(
            status_code=status_code,
            detail=f"User with {user_param} is not found.",
        )


class UserAlreadyExist(HTTPException):
    def __init__(self, username: str) -> None:
        msg = f"User with {username=} already exists."
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=msg)


class InvalidOldPassword(HTTPException):
    def __init__(self) -> None:
        msg = "Not correct old password, it's not equal to already existing password."
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=msg)


class BadRequestCreatingUser(HTTPException):
    def __init__(self, exc: str) -> None:
        msg = f"Can't create user: {exc}"
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=msg)


class BadRequestUpdatingUser(HTTPException):
    def __init__(self, exc: str) -> None:
        msg = f"Can't update user: {exc}"
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=msg)
