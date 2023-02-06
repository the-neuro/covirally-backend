from sqlalchemy import Column, String, Boolean, DateTime, func, text

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(  # noqa
        String, primary_key=True, server_default=text("gen_random_uuid()::varchar")
    )

    first_name = Column(String(length=64), nullable=False)
    last_name = Column(String(length=64), nullable=False)

    username = Column(String(length=64), unique=True, index=True, nullable=True)
    password = Column(String(length=256), nullable=True)
    avatar_url = Column(String, nullable=True)

    email = Column(String(length=128))
    telephone_number = Column(String(length=12), nullable=True)

    receive_email_alerts = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
