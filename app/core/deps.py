from loguru import logger
from typing import Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from jwt import PyJWTError
from jwt.exceptions import PyJWKClientError

from app.core.auth0 import verify_auth0_token, extract_email
from app.core.errors import TokenDecodeError, InvalidCredentials, Forbidden
from app.db.database import get_db
from app.models import User
from app.repositories.user_repo import user_repo
from app.services.auth_service import AuthService, decode_access_token

bearer = HTTPBearer(auto_error=False)


async def get_current_identity(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    logger.info("get_current_identity: raw creds = %s", creds)

    if creds is None or creds.scheme.lower() != "bearer":
        raise TokenDecodeError("Missing bearer token")

    token = creds.credentials

    try:
        header = jwt.get_unverified_header(token)
    except PyJWTError as ex:
        logger.warning(
            "get_current_identity: failed to parse JWT header: %s",
            ex
        )
        raise TokenDecodeError("Invalid token")

    alg = header.get("alg")
    kid = header.get("kid")
    logger.info("get_current_identity: header alg=%s kid=%s", alg, kid)

    if alg == "RS256" or kid is not None:
        logger.info("get_current_identity: treating token as Auth0")
        try:
            claims = verify_auth0_token(token)
            email = extract_email(claims)
            logger.info("get_current_identity: Auth0 OK, email=%s", email)
            return {
                "email": email,
                "source": "auth0",
                "payload": claims,
            }
        except (PyJWKClientError, PyJWTError, HTTPException) as ex:
            logger.warning(
                "get_current_identity: Auth0 verification failed: %s",
                ex
            )
            raise TokenDecodeError("Invalid Auth0 token")

    logger.info("get_current_identity: treating token as local JWT (HS256)")
    try:
        payload = decode_access_token(token)
    except TokenDecodeError as ex:
        logger.warning("get_current_identity: local JWT decode failed: %s", ex)
        raise TokenDecodeError("Invalid token")

    email = payload.get("email")
    if not email:
        raise TokenDecodeError("Email not found in token")

    logger.info("get_current_identity: local JWT OK, email=%s", email)
    return {
        "email": email,
        "source": "local",
        "payload": payload,
    }


async def get_current_user_auth0(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    if creds is None or creds.scheme.lower() != "bearer":
        raise InvalidCredentials("Missing bearer token")

    token = creds.credentials
    claims = verify_auth0_token(token)
    email = extract_email(claims)

    user = await user_repo.get_by_email(db, email)
    if not user:
        user = await user_repo.create_from_email(db, email)

    return user


async def get_current_user_email(
    payload: Dict[str, Any] = Depends(get_current_identity),
) -> str:
    email = extract_email(payload)
    if not email:
        raise TokenDecodeError("Email claim not found")
    return email


async def optional_current_user_dep(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    try:
        if creds is None or creds.scheme.lower() != "bearer":
            return None

        claims = verify_auth0_token(creds.credentials)
        email = extract_email(claims)
        if not email:
            return None

        user = await user_repo.get_by_email(db, email)
        return user
    except Exception:
        return None


def auth_service_dep(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db=db)


async def get_current_user(
    identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> User:

    email = identity.get("email")
    source = identity.get("source")
    payload = identity.get("payload") or {}

    if source == "auth0":
        if not email:
            raise TokenDecodeError("Email is not found in the token")

        user = await user_repo.get_by_email(db, email)
        if not user:
            user = await user_repo.create_from_email(db, email=email)
        return user

    if source == "local":
        sub = payload.get("sub")
        if not sub:
            raise TokenDecodeError("Invalid local token subject")

        try:
            user_id = int(sub)
        except ValueError:
            raise TokenDecodeError("Invalid local token subject")

        user = await user_repo.get_by_id(db, user_id)
        if not user:
            raise InvalidCredentials("Invalid credentials")

        if getattr(user, "is_active", True) is False:
            raise Forbidden("User inactive")

        return user

    raise InvalidCredentials("Unknown auth source")
