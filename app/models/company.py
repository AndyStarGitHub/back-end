from __future__ import annotations

from uuid import uuid4
from sqlalchemy import Column, String, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base

class CompanyVisibilityEnum(str):
    HIDDEN = "hidden"
    PUBLIC = "public"


class Company(Base):
    __tablename__ = "companies"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)

    visibility = Column(
        String(20),
        nullable=False,
        default=CompanyVisibilityEnum.HIDDEN,
    )

    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    owner = relationship("User")
