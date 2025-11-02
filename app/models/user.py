from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, event
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.utils.utils import now_kyiv


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=now_kyiv,
    )


@event.listens_for(User, "before_insert")
def _ensure_created_at(mapper, connection, target):
    if target.created_at is None or target.created_at.tzinfo is None:
        target.created_at = now_kyiv()
