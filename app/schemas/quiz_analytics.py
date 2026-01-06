from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserQuizAverageInRange(BaseModel):
    quiz_id: UUID
    company_id: UUID
    average_score: float
    total_questions: int
    total_correct_answers: int
    attempts_count: int
    period_from: datetime | None = None
    period_to: datetime | None = None


class UserQuizAverageList(BaseModel):
    user_id: int
    items: list[UserQuizAverageInRange]


class UserQuizLastAttempt(BaseModel):
    quiz_id: UUID
    company_id: UUID
    last_attempt_at: datetime | None = None


class UserQuizLastAttemptList(BaseModel):
    user_id: int
    items: list[UserQuizLastAttempt]


class CompanyWeeklyStatsItem(BaseModel):
    week_start: datetime
    average_score: float
    total_questions: int
    total_correct_answers: int
    attempts_count: int


class CompanyWeeklyStats(BaseModel):
    company_id: UUID
    items: list[CompanyWeeklyStatsItem]


class CompanyUserQuizWeeklyItem(BaseModel):
    quiz_id: UUID
    week_start: datetime
    average_score: float
    total_questions: int
    total_correct_answers: int
    attempts_count: int


class CompanyUserQuizWeeklyStats(BaseModel):
    company_id: UUID
    user_id: int
    items: list[CompanyUserQuizWeeklyItem]


class CompanyUserLastAttempt(BaseModel):
    user_id: int
    last_attempt_at: datetime | None = None


class CompanyUsersLastAttemptList(BaseModel):
    company_id: UUID
    items: list[CompanyUserLastAttempt]


class GlobalRatingStats(BaseModel):
    average_score: float
    total_questions: int
    total_correct_answers: int
    attempts_count: int


class MyQuizWeeklyItem(BaseModel):
    quiz_id: UUID
    week_start: datetime
    average_score: float
    total_questions: int
    total_correct_answers: int
    attempts_count: int


class MyQuizWeeklyStats(BaseModel):
    user_id: int
    items: list[MyQuizWeeklyItem]


class CompanyQuizLastAttemptItem(BaseModel):
    quiz_id: UUID
    last_attempt_at: datetime | None = None


class CompanyQuizLastAttemptList(BaseModel):
    company_id: UUID
    items: list[CompanyQuizLastAttemptItem]
