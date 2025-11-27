from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class QuizFrequency(str, Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"
    custom = "custom"


class QuizAnswerOptionBase(BaseModel):
    text: str
    is_correct: bool


class QuizAnswerOptionCreate(QuizAnswerOptionBase):
    pass


class QuizAnswerOptionRead(QuizAnswerOptionBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class QuizQuestionBase(BaseModel):
    title: str


class QuizQuestionCreate(QuizQuestionBase):
    options: list[QuizAnswerOptionCreate]


class QuizQuestionRead(QuizQuestionBase):
    id: UUID
    options: list[QuizAnswerOptionRead]

    model_config = ConfigDict(from_attributes=True)


class QuizBase(BaseModel):
    title: str
    description: str | None = None


class QuizCreate(QuizBase):
    frequency: QuizFrequency = QuizFrequency.monthly
    questions: list[QuizQuestionCreate]


class QuizUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    frequency: QuizFrequency | None = None
    questions: list[QuizQuestionCreate] | None = None


class QuizRead(BaseModel):
    id: UUID
    company_id: UUID
    title: str
    description: str | None
    frequency: QuizFrequency
    questions: list[QuizQuestionRead]

    model_config = ConfigDict(from_attributes=True)


class QuizListResponse(BaseModel):
    total: int
    items: list[QuizRead]
    offset: int
    limit: int


class QuizSubmit(BaseModel):
    answers: list[QuizAnswerSubmit]


class QuizAnswerSubmit(BaseModel):
    question_id: UUID
    selected_option_ids: list[UUID]


class QuizAttemptRead(BaseModel):
    id: UUID
    user_id: int
    company_id: UUID
    quiz_id: UUID
    total_questions: int
    correct_answers: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserQuizStats(BaseModel):
    user_id: int
    total_questions_answered: int
    total_correct_answers: int
    average_score: float
    last_attempt_at: datetime | None = None
