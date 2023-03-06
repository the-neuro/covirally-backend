from enum import Enum


class TaskStatus(str, Enum):
    IDEA = "idea"
    IN_PROGRESS = "in_progress"
    DONE = "done"
