import uuid

from sqlalchemy import Column, String, Boolean, DateTime, func

from app.db.base import Base


def _uuid4() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid4)  # noqa

    first_name = Column(String(length=64), nullable=False)
    last_name = Column(String(length=64), nullable=False)

    username = Column(String(length=64), unique=True, index=True, nullable=True)
    password = Column(String(length=256), nullable=True)
    avatar_url = Column(String, nullable=True)

    email = Column(String(length=128))
    telephone_number = Column(String(length=12), nullable=True)

    receive_email_alerts = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
