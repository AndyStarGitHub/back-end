from sqlalchemy import (
    String,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    company_memberships: Mapped[list["CompanyMember"]] = relationship(
        "CompanyMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    company_invitations: Mapped[list["CompanyInvitation"]] = relationship(
        "CompanyInvitation",
        foreign_keys="CompanyInvitation.invited_user_id",
        back_populates="invited_user",
        cascade="all, delete-orphan",
    )

    sent_company_invitations: Mapped[list["CompanyInvitation"]] = relationship(
        "CompanyInvitation",
        foreign_keys="CompanyInvitation.invited_by_id",
        back_populates="invited_by",
        cascade="all, delete-orphan",
    )

    company_join_requests: Mapped[list["CompanyJoinRequest"]] = relationship(
        "CompanyJoinRequest",
        back_populates="user",
        cascade="all, delete-orphan",
    )

