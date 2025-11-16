from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .errors import (
    AppError, NotAuthenticated, InvalidCredentials, TokenInvalid,
    Forbidden, NotFound, Conflict
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotAuthenticated)
    async def _401(_req, exc: NotAuthenticated):
        return JSONResponse(
            status_code=401,
            content={"detail": str(exc) or "Not authenticated"}
        )

    @app.exception_handler(InvalidCredentials)
    async def _401_creds(_req, exc: InvalidCredentials):
        return JSONResponse(
            status_code=401,
            content={"detail": str(exc) or "Invalid credentials"}
        )

    @app.exception_handler(TokenInvalid)
    async def _401_token(_req, exc: TokenInvalid):
        return JSONResponse(
            status_code=401,
            content={"detail": str(exc) or "Invalid token"}
        )

    @app.exception_handler(Forbidden)
    async def _403(_req, exc: Forbidden):
        return JSONResponse(
            status_code=403,
            content={"detail": str(exc) or "Forbidden"}
        )

    @app.exception_handler(NotFound)
    async def _404(_req, exc: NotFound):
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc) or "Not found"}
        )

    @app.exception_handler(Conflict)
    async def _409(_req, exc: Conflict):
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc) or "Conflict"}
        )

    @app.exception_handler(AppError)
    async def _400(_req, exc: AppError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc) or "Bad request"}
        )
