from enum import Enum
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.mixins import UUIDMixin, TimestampedMixin


class CompanyVisibilityEnum(str, Enum):
    HIDDEN = "hidden"
    PUBLIC = "public"


class Company(UUIDMixin, TimestampedMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    visibility: Mapped[str] = mapped_column(
        String(20),
        default=CompanyVisibilityEnum.PUBLIC.value,
        nullable=False,
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    owner = relationship("User")

    members = relationship(
        "CompanyMember",
        back_populates="company",
        cascade="all, delete-orphan",
    )

    join_requests = relationship(
        "CompanyJoinRequest",
        back_populates="company",
        cascade="all, delete-orphan",
    )

    invitations = relationship(
        "CompanyInvitation",
        back_populates="company",
        cascade="all, delete-orphan",
    )
