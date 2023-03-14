from sqlalchemy import String, text, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class Hashtag(Base):
    __tablename__ = "hashtags"

    id = Column(  # noqa
        String, primary_key=True, server_default=text("gen_random_uuid()::varchar")
    )

    hashtag = Column(String(length=20), nullable=False)

    task_id = Column(String, ForeignKey("tasks.id"), index=True, nullable=False)
    assignee = relationship("Task", foreign_keys=[task_id], backref="hashtags")
