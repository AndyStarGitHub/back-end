from enum import Enum
from sqlalchemy import ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.mixins import UUIDMixin, TimestampedMixin


class CompanyJoinRequestStatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELED = "canceled"


class CompanyJoinRequest(UUIDMixin, TimestampedMixin, Base):
    __tablename__ = "company_join_requests"

    company_id: Mapped[str] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[CompanyJoinRequestStatusEnum] = mapped_column(
        SAEnum(
            CompanyJoinRequestStatusEnum,
            name="company_join_request_status",
            native_enum=False,
        ),
        default=CompanyJoinRequestStatusEnum.PENDING,
        nullable=False,
    )

    company = relationship("Company", back_populates="join_requests")
    user = relationship("User", back_populates="company_join_requests")
