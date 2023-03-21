from http import HTTPStatus

from fastapi import HTTPException


class InvalidAuthorization(HTTPException):
    def __init__(self, msg: str) -> None:
        super().__init__(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail=msg,
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
    def __init__(self, param: str) -> None:
        msg = f"User with {param=} already exists."
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


class BadRequestCreatingTask(HTTPException):
    def __init__(self, exc: str) -> None:
        msg = f"Can't create task: {exc}"
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=msg)


class BadRequestAddingCommentToTask(HTTPException):
    def __init__(self, exc: str) -> None:
        msg = f"Can't add comment to task: {exc}"
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=msg)


class InvalidCreatorSuggesterIds(HTTPException):
    def __init__(self, exc: str) -> None:
        msg = f"Can't create task: {exc}"
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=msg)


class BadRequestUpdatingTask(HTTPException):
    def __init__(self, exc: str) -> None:
        msg = f"Can't update task: {exc}"
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=msg)


class BadRequestDeletingTask(HTTPException):
    def __init__(self, exc: str) -> None:
        msg = f"Can't delete task: {exc}"
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=msg)


class TaskNotFound(HTTPException):
    def __init__(self, task_id: str) -> None:
        msg = f"No task with {task_id=}"
        super().__init__(status_code=HTTPStatus.NOT_FOUND, detail=msg)


class NotCreatorPermissionError(HTTPException):
    def __init__(self) -> None:
        msg = "Only creator is allowed to do it."
        super().__init__(status_code=HTTPStatus.FORBIDDEN, detail=msg)


class InvalidVerifyEmailToken(HTTPException):
    def __init__(self) -> None:
        msg = "Token is invalid."
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=msg)


class EmailIsAlreadyVerified(HTTPException):
    def __init__(self, email: str) -> None:
        msg = f"Email {email} is already verified."
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=msg)


class RefreshPasswordTokenIsExpired(HTTPException):
    def __init__(self) -> None:
        msg = "Refresh password token is expired."
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=msg)


class InvalidRefreshPasswordToken(HTTPException):
    def __init__(self) -> None:
        msg = "Refresh password token is invalid."
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=msg)


class ForbiddenUpdateComment(HTTPException):
    def __init__(self) -> None:
        msg = "Can't update comment"
        super().__init__(status_code=HTTPStatus.FORBIDDEN, detail=msg)


class ForbiddenDeleteComment(HTTPException):
    def __init__(self) -> None:
        msg = "Can't delete comment"
        super().__init__(status_code=HTTPStatus.FORBIDDEN, detail=msg)


class CommentNotFound(HTTPException):
    def __init__(self, comment_id: str) -> None:
        msg = f"No comment with {comment_id=}"
        super().__init__(status_code=HTTPStatus.NOT_FOUND, detail=msg)


class BadRequestUpdatingComment(HTTPException):
    def __init__(self, exc: str) -> None:
        msg = f"Can't update comment: {exc}"
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=msg)
