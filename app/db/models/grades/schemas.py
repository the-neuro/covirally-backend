from sqlalchemy import String, text, Column, ForeignKey, DateTime, Enum, JSON, Integer

from app.db.base import Base
from app.types import Grades


class Grade(Base):
    __tablename__ = "grades"

    id = Column(  # noqa
        String, primary_key=True, server_default=text("gen_random_uuid()::varchar")
    )

    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    creator_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    grade_variant = Column(
        Enum(Grades, name="grade_variant"),
        default=Grades.SUBSCRIBED.value,
        nullable=False,
    )
    grade_variant_int = Column(Integer, default=-1, nullable=False)
    grade_rights = Column(JSON, nullable=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True, nullable=True)
    degrades_at = Column(DateTime(timezone=True), nullable=True)
