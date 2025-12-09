from __future__ import annotations

from enum import Enum
from uuid import UUID

from sqlalchemy import String, ForeignKey, Boolean, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.mixins import UUIDMixin, TimestampedMixin


class QuizFrequencyEnum(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class Quiz(UUIDMixin, TimestampedMixin, Base):
    __tablename__ = "quizzes"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    frequency: Mapped[QuizFrequencyEnum] = mapped_column(
        SqlEnum(
            QuizFrequencyEnum,
            name="quiz_frequency_enum",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=QuizFrequencyEnum.MONTHLY,
        nullable=False,
    )

    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(
        "Company",
        back_populates="quizzes",
    )

    questions: Mapped[list["QuizQuestion"]] = relationship(
        "QuizQuestion",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )

    attempts: Mapped[list["QuizAttempt"]] = relationship(
        "QuizAttempt",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )

    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )


class QuizQuestion(UUIDMixin, TimestampedMixin, Base):
    __tablename__ = "quiz_questions"

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    quiz_id: Mapped[UUID] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
    )

    quiz: Mapped["Quiz"] = relationship(
        "Quiz",
        back_populates="questions",
    )

    options: Mapped[list["QuizAnswerOption"]] = relationship(
        "QuizAnswerOption",
        back_populates="question",
        cascade="all, delete-orphan",
    )


class QuizAnswerOption(UUIDMixin, TimestampedMixin, Base):
    __tablename__ = "quiz_answer_options"

    text: Mapped[str] = mapped_column(String(255), nullable=False)

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    question_id: Mapped[UUID] = mapped_column(
        ForeignKey("quiz_questions.id", ondelete="CASCADE"),
        nullable=False,
    )

    question: Mapped["QuizQuestion"] = relationship(
        "QuizQuestion",
        back_populates="options",
    )
