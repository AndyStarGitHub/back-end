from sqlalchemy import ForeignKey, UniqueConstraint, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.mixins import UUIDMixin, TimestampedMixin

from enum import Enum


class CompanyMemberRoleEnum(str, Enum):
    MEMBER = "member"
    ADMIN = "admin"


class CompanyMember(UUIDMixin, TimestampedMixin, Base):
    __tablename__ = "company_members"

    company_id: Mapped[str] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[CompanyMemberRoleEnum] = mapped_column(
        SqlEnum(
            CompanyMemberRoleEnum,
            name="company_member_role",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=CompanyMemberRoleEnum.MEMBER,
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "user_id",
            name="uq_company_members_company_id_user_id",
        ),
    )

    company = relationship("Company", back_populates="members")
    user = relationship("User", back_populates="company_memberships")
