from sqlalchemy import Column, String, Enum, DateTime, func, text, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.types import TaskStatus


class Task(Base):
    __tablename__ = "tasks"

    id = Column(  # noqa
        String, primary_key=True, server_default=text("gen_random_uuid()::varchar")
    )

    title = Column(String(length=128), nullable=False)
    description = Column(String(length=1024), nullable=True)

    due_to_date = Column(DateTime(timezone=True), nullable=True)

    status = Column(
        Enum(TaskStatus, name="taskstatus"),
        default=TaskStatus.IDEA.value,
        nullable=False,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # blogger, producer, writer -- creator of content
    creator_id = Column(String, ForeignKey("users.id"), nullable=False)

    # any user can suggest a task to creator
    suggested_by_id = Column(String, ForeignKey("users.id"), nullable=True)

    # some user might be responsible for an execution of task
    assignee_id = Column(String, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)

    creator = relationship("User", foreign_keys=[creator_id], backref="tasks")
    suggested_by = relationship(
        "User", foreign_keys=[suggested_by_id], backref="suggested_tasks"
    )
    assignee = relationship("User", foreign_keys=[assignee_id], backref="asigned_tasks")


class TaskComment(Base):
    __tablename__ = "tasks_comments"

    id = Column(  # noqa
        String, primary_key=True, server_default=text("gen_random_uuid()::varchar")
    )

    content = Column(String(length=2000), nullable=False)

    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    task = relationship("Task", foreign_keys=[task_id], backref="comments")

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    user = relationship("User", foreign_keys=[user_id], backref="task_comments")

    edited = Column(Boolean, server_default="0", default=False, nullable=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
