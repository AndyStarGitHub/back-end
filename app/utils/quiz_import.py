from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from app.schemas.quiz import QuizFrequency


def canon_header(st: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (st or "").strip().lower())


def norm_text(st: str) -> str:
    return " ".join((st or "").strip().lower().split())


def parse_bool(bo: Any) -> bool:
    if isinstance(bo, bool):
        return bo
    if bo is None:
        raise ValueError("is_correct is required")

    if isinstance(bo, (int, float)):
        if bo == 1:
            return True
        if bo == 0:
            return False

    bosl = str(bo).strip().lower()
    if bosl in {"true", "t", "1", "yes", "y", "+", "correct"}:
        return True
    if bosl in {"false", "f", "0", "no", "n", "-", "wrong"}:
        return False

    raise ValueError(f"Invalid boolean value: {bo!r}")


def parse_uuid(ui: Any) -> UUID | None:
    if ui is None or str(ui).strip() == "":
        return None
    try:
        return UUID(str(ui).strip())
    except Exception:
        raise ValueError(f"Invalid UUID: {ui!r}")


def parse_frequency(fr: Any) -> QuizFrequency:
    if fr is None or str(fr).strip() == "":
        return QuizFrequency.monthly

    st = str(fr).strip().lower()
    allowed = {e.value: e for e in QuizFrequency}
    if st not in allowed:
        raise ValueError(f"Invalid quiz_frequency: {fr!r}")
    return allowed[st]
