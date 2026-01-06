from fastapi import APIRouter

from .ping import router as ping_router
from .health import router as health_router
from app.api.users import router as users_router
from app.api.auth import router as auth_router
from app.api.companies import router as companies_router
from app.api.company_invitations import router as company_invitations_router
from app.api.company_members import router as company_members_router
from app.api.company_join_requests import (
    router as company_join_requests_router
)
from app.api.quizzes import router as quizzes_router
from app.api.quiz_analytics import router as quiz_analytics_router
from app.api.company_quiz_analytics import (
    router as company_quiz_analytics_router,
)
from app.api.notifications import router as notifications_router
from app.api.notifications_ws import router as notifications_ws_router
from app.api.quiz_analytics_public import (
    router as quiz_analytics_public_router)
from app.api.quiz_attempt_exports_db import (
    router as quiz_attempt_exports_db_router
)


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["diagnostics"]
)
api_router.include_router(
    ping_router,
    prefix="/ping",
    tags=["diagnostics"]
)
api_router.include_router(
    users_router,
    prefix="/users",
    tags=["users"]
)
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"]
)
api_router.include_router(
    companies_router,
    prefix="/companies",
    tags=["companies"]
)
api_router.include_router(
    company_invitations_router,
    prefix="/company-invitations",
    tags=["company-invitations"]
)
api_router.include_router(
    company_members_router,
    prefix="/company-members",
    tags=["company-members"]
)
api_router.include_router(
    company_join_requests_router,
    prefix="/company-join-requests",
    tags=["company-join-requests"]
)
api_router.include_router(
    quizzes_router,
    prefix="/me/quiz",
    tags=["quizzes"],
)
api_router.include_router(
    quiz_analytics_router,
    prefix="/me/quiz_analytics",
    tags=["quiz-analytics"],
)
api_router.include_router(
    company_quiz_analytics_router,
    prefix="/companies/{company_id}/quiz-analytics",
    tags=["company-quiz-analytics"],
)
api_router.include_router(
    notifications_router,
    prefix="/me/notifications",
    tags=["notifications"],
)
api_router.include_router(
    notifications_ws_router,
    tags=["notifications-ws"],
)
api_router.include_router(
    quiz_analytics_public_router,
    prefix="/quiz_analytics",
    tags=["quiz-analytics-public"],
)
api_router.include_router(
    quiz_attempt_exports_db_router,
    prefix="",
    tags=["quiz-attempts-export-db"],
)


__all__ = ["api_router"]
