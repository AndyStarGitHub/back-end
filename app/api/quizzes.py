from typing import Literal
from fastapi import APIRouter, Depends, UploadFile, File
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user, get_quiz_service
from app.services.quiz import QuizService


ExportFormat = Literal["json", "csv"]

router = APIRouter(
    prefix="/companies/{company_id}/quizzes",
    tags=["quizzes"],
)


from fastapi import Response
from fastapi.responses import JSONResponse


def _build_export_http_response(
    *,
    format: ExportFormat,
    result,
    filename: str,
) -> Response:

    if format == "json":
        return JSONResponse(
            content=result,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )

    return Response(
        content=result,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )


@router.get("/export/my")
async def export_my_quiz_attempts(
    company_id: UUID,
    format: ExportFormat = "json",
    quiz_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
):

    result = await quiz_service.export_my_attempts_for_company(
        db,
        company_id=company_id,
        current_user=current_user,
        format=format,
        quiz_id=quiz_id,
    )

    filename = f"quiz_export_my_{company_id}.{format}"

    return _build_export_http_response(
        format=format,
        result=result,
        filename=filename,
    )


@router.get("/export/users/{user_id}")
async def export_user_quiz_attempts(
    company_id: UUID,
    user_id: int,
    format: ExportFormat = "json",
    quiz_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
):

    result = await quiz_service.export_user_attempts_for_company(
        db,
        company_id=company_id,
        current_user=current_user,
        target_user_id=user_id,
        format=format,
        quiz_id=quiz_id,
    )

    filename = f"quiz_export_user_{user_id}_company_{company_id}.{format}"
    return _build_export_http_response(
        format=format,
        result=result,
        filename=filename,
    )


@router.get("/export/company")
async def export_company_quiz_attempts(
    company_id: UUID,
    format: ExportFormat = "json",
    quiz_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
):

    result = await quiz_service.export_company_attempts(
        db,
        company_id=company_id,
        current_user=current_user,
        format=format,
        quiz_id=quiz_id,
    )

    filename = f"quiz_export_company_{company_id}.{format}"
    return _build_export_http_response(
        format=format,
        result=result,
        filename=filename,
    )


@router.post("/import")
async def import_quizzes_from_excel(
    company_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
):
    file_bytes = await file.read()

    result = await quiz_service.import_quizzes_from_excel(
        db,
        company_id=company_id,
        current_user=current_user,
        file_bytes=file_bytes,
    )

    return result
