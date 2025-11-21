from enum import Enum
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.mixins import UUIDMixin, TimestampedMixin


class CompanyInvitationStatusEnum(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELED = "canceled"


class CompanyInvitation(UUIDMixin, TimestampedMixin, Base):
    __tablename__ = "company_invitations"

    company_id: Mapped[str] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    invited_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    invited_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default=CompanyInvitationStatusEnum.PENDING.value,
        nullable=False,
    )

    company = relationship("Company", back_populates="invitations")

    invited_user = relationship(
        "User",
        foreign_keys=[invited_user_id],
        back_populates="company_invitations",
    )

    invited_by = relationship(
        "User",
        foreign_keys=[invited_by_id],
        back_populates="sent_company_invitations",
    )
