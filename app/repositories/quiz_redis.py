from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from redis.asyncio import Redis

from app.models.quiz_attempt import QuizAttempt


class QuizRedisRepository:

    def __init__(self, redis: Redis, ttl_seconds: int = 48 * 60 * 60) -> None:

        self.redis = redis
        self.ttl_seconds = ttl_seconds

    def _build_key(self, attempt_id: UUID) -> str:

        return f"quiz:attempt:{attempt_id}"

    def _serialize_datetime(self, dt: datetime | None) -> str | None:

        if dt is None:
            return None
        return dt.isoformat()

    def _build_payload(self, attempt: QuizAttempt) -> dict[str, Any]:

        answers: list[dict[str, Any]] = []

        for answer in attempt.answers:
            selected_option_ids = [
                str(sel.option_id)
                for sel in answer.selected_options
            ]

            answers.append(
                {
                    "question_id": str(answer.question_id),
                    "selected_option_ids": selected_option_ids,
                    "is_correct": answer.is_correct,
                }
            )

        return {
            "attempt_id": str(attempt.id),
            "user_id": attempt.user_id,
            "company_id": str(attempt.company_id),
            "quiz_id": str(attempt.quiz_id),
            "total_questions": attempt.total_questions,
            "correct_answers": attempt.correct_answers,
            "created_at": self._serialize_datetime(attempt.created_at),
            "answers": answers,
        }

    async def save_attempt(self, attempt: QuizAttempt) -> None:

        key = self._build_key(attempt.id)
        payload = self._build_payload(attempt)
        await self.redis.set(key, json.dumps(payload), ex=self.ttl_seconds)

    async def get_attempt(self, attempt_id: UUID) -> dict[str, Any] | None:

        key = self._build_key(attempt_id)
        raw = await self.redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def delete_attempt(self, attempt_id: UUID) -> None:

        key = self._build_key(attempt_id)
        await self.redis.delete(key)
