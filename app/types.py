from enum import Enum


EMAIL_REGEX = r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"


class TaskStatus(str, Enum):
    IDEA = "idea"
    IN_PROGRESS = "in_progress"
    DONE = "done"
