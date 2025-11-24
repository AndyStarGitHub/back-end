from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.mixins import UUIDMixin, TimestampedMixin


class QuizAttempt(UUIDMixin, TimestampedMixin, Base):
    __tablename__ = "quiz_attempts"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    quiz_id: Mapped[UUID] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # агреговані значення по цій спробі
    total_questions: Mapped[int] = mapped_column(nullable=False)
    correct_answers: Mapped[int] = mapped_column(nullable=False)

    # relationships
    user = relationship("User")
    company = relationship("Company")
    quiz = relationship("Quiz", back_populates="attempts")

    answers: Mapped[list["QuizAttemptAnswer"]] = relationship(
        "QuizAttemptAnswer",
        back_populates="attempt",
        cascade="all, delete-orphan",
    )


class QuizAttemptAnswer(UUIDMixin, TimestampedMixin, Base):
    __tablename__ = "quiz_attempt_answers"

    attempt_id: Mapped[UUID] = mapped_column(
        ForeignKey("quiz_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )

    question_id: Mapped[UUID] = mapped_column(
        ForeignKey("quiz_questions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # чи відповідь на це питання була повністю правильною
    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    attempt: Mapped["QuizAttempt"] = relationship(
        "QuizAttempt",
        back_populates="answers",
    )

    question = relationship("QuizQuestion")

    selected_options: Mapped[list["QuizAttemptAnswerOption"]] = relationship(
        "QuizAttemptAnswerOption",
        back_populates="attempt_answer",
        cascade="all, delete-orphan",
    )


class QuizAttemptAnswerOption(UUIDMixin, TimestampedMixin, Base):
    __tablename__ = "quiz_attempt_answer_options"

    attempt_answer_id: Mapped[UUID] = mapped_column(
        ForeignKey("quiz_attempt_answers.id", ondelete="CASCADE"),
        nullable=False,
    )

    option_id: Mapped[UUID] = mapped_column(
        ForeignKey("quiz_answer_options.id", ondelete="CASCADE"),
        nullable=False,
    )

    attempt_answer: Mapped["QuizAttemptAnswer"] = relationship(
        "QuizAttemptAnswer",
        back_populates="selected_options",
    )

    option = relationship("QuizAnswerOption")
