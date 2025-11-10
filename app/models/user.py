from sqlalchemy import (
    String,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.models.mixins import IdMixin, TimestampedMixin


class User(IdMixin, TimestampedMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
