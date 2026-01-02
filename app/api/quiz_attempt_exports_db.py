from __future__ import annotations

import json
from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user, get_quiz_service
from app.services.quiz import QuizService

router = APIRouter()


def _today_ymd() -> str:
    return date.today().isoformat()


def _build_filename(
    *,
    kind: Literal["my", "company", "user"],
    company_id: UUID,
    ext: Literal["csv", "json"],
    user_id: int | None = None,
    quiz_id: UUID | None = None,
) -> str:
    ymd = _today_ymd()

    if kind == "my":
        base = f"my_quiz_attempts_{company_id}_{ymd}"
    elif kind == "company":
        base = f"company_quiz_attempts_{company_id}_{ymd}"
    else:
        base = f"user_{user_id}_quiz_attempts_{company_id}_{ymd}"

    if quiz_id is not None:
        base += f"_quiz_{quiz_id}"

    return f"{base}.{ext}"


def _file_response(
    *,
    content: bytes,
    media_type: str,
    filename: str,
) -> Response:
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return Response(content=content, media_type=media_type, headers=headers)


@router.get("/me/quiz-attempts/export/db")
async def export_my_attempts_db(
    company_id: UUID,
    format: Literal["csv", "json"] = "json",
    quiz_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
):
    data = await quiz_service.export_my_attempts_for_company_db(
        db,
        company_id=company_id,
        current_user=current_user,
        format=format,
        quiz_id=quiz_id,
    )

    filename = _build_filename(
        kind="my",
        company_id=company_id,
        user_id=current_user.id,
        quiz_id=quiz_id,
        ext=format,
    )

    if format == "csv":
        return _file_response(
            content=str(data).encode("utf-8"),
            media_type="text/csv; charset=utf-8",
            filename=filename,
        )

    json_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return _file_response(
        content=json_bytes,
        media_type="application/json; charset=utf-8",
        filename=filename,
    )


@router.get("/companies/{company_id}/quiz-attempts/export/db")
async def export_company_attempts_db(
    company_id: UUID,
    format: Literal["csv", "json"] = "json",
    quiz_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
):
    data = await quiz_service.export_company_attempts_db(
        db,
        company_id=company_id,
        current_user=current_user,
        format=format,
        quiz_id=quiz_id,
    )

    filename = _build_filename(
        kind="company",
        company_id=company_id,
        quiz_id=quiz_id,
        ext=format,
    )

    if format == "csv":
        return _file_response(
            content=str(data).encode("utf-8"),
            media_type="text/csv; charset=utf-8",
            filename=filename,
        )

    json_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return _file_response(
        content=json_bytes,
        media_type="application/json; charset=utf-8",
        filename=filename,
    )


@router.get("/companies/{company_id}/users/{user_id}/quiz-attempts/export/db")
async def export_company_user_attempts_db(
    company_id: UUID,
    user_id: int,
    format: Literal["csv", "json"] = "json",
    quiz_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
):
    data = await quiz_service.export_user_attempts_for_company_db(
        db,
        company_id=company_id,
        current_user=current_user,
        target_user_id=user_id,
        format=format,
        quiz_id=quiz_id,
    )

    filename = _build_filename(
        kind="user",
        company_id=company_id,
        user_id=user_id,
        quiz_id=quiz_id,
        ext=format,
    )

    if format == "csv":
        return _file_response(
            content=str(data).encode("utf-8"),
            media_type="text/csv; charset=utf-8",
            filename=filename,
        )

    json_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return _file_response(
        content=json_bytes,
        media_type="application/json; charset=utf-8",
        filename=filename,
    )
