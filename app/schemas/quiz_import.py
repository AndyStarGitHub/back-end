from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.quiz import QuizCreate, QuizFrequency


class ImportErrorItem(BaseModel):
    row: int = Field(ge=1)
    field: str
    message: str


class ParsedQuizItem(BaseModel):
    quiz_id: UUID | None
    title: str
    description: str | None
    frequency: QuizFrequency
    quiz_title_norm: str
    quiz_create: QuizCreate
    first_row: int = Field(ge=1)


class ParsedImportResult(BaseModel):
    items: list[ParsedQuizItem]
    errors: list[ImportErrorItem]
    total_quizzes_in_file: int = Field(ge=0)

    model_config = ConfigDict(arbitrary_types_allowed=True)
