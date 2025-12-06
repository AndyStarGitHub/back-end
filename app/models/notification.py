from __future__ import annotations

from enum import Enum
from uuid import UUID

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SqlEnum

from app.db.database import Base
from app.models.mixins import UUIDMixin, TimestampedMixin


class NotificationStatusEnum(str, Enum):
    UNREAD = "unread"
    READ = "read"


class Notification(UUIDMixin, TimestampedMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    company_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
    )

    quiz_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=True,
    )

    message: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[NotificationStatusEnum] = mapped_column(
        SqlEnum(
            NotificationStatusEnum,
            name="notification_status_enum",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=NotificationStatusEnum.UNREAD,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications",
    )

    company: Mapped["Company"] = relationship(
        "Company",
        back_populates="notifications",
    )

    quiz: Mapped["Quiz"] = relationship(
        "Quiz",
        back_populates="notifications",
    )
