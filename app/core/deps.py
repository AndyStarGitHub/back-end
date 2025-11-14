from loguru import logger
from typing import Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from jwt import PyJWTError
from jwt.exceptions import PyJWKClientError

from app.core.auth0 import verify_auth0_token, extract_email
from app.core.errors import TokenInvalid, NotFound
from app.db.database import get_db
from app.models import User
from app.repositories.user_repo import user_repo
from app.services.auth_service import AuthService
from app.core.jwt import decode_access_token, TokenDecodeError

bearer = HTTPBearer(auto_error=False)


async def get_current_identity(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    logger.info("get_current_identity: raw creds = %s", creds)

    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    token = creds.credentials

    # 1️⃣ Дивимось у заголовок токена, щоб зрозуміти, що це за токен
    try:
        header = jwt.get_unverified_header(token)
    except PyJWTError as e:
        logger.warning("get_current_identity: failed to parse JWT header: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    alg = header.get("alg")
    kid = header.get("kid")
    logger.info("get_current_identity: header alg=%s kid=%s", alg, kid)

    # 2️⃣ Якщо токен схожий на Auth0 (RS256 і/або є kid) → пробуємо Auth0
    if alg == "RS256" or kid is not None:
        logger.info("get_current_identity: treating token as Auth0")
        try:
            claims = verify_auth0_token(token)  # тут вже RS256 + PyJWKClient
            email = extract_email(claims)
            logger.info("get_current_identity: Auth0 OK, email=%s", email)
            return {
                "email": email,
                "source": "auth0",
                "payload": claims,
            }
        except (PyJWKClientError, PyJWTError, HTTPException) as e:
            logger.warning("get_current_identity: Auth0 verification failed: %s", e)
            # для Auth0-токена fallback на локальний сенсу не має → 401
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Auth0 token",
            )

    # 3️⃣ Інакше вважаємо, що це наш локальний JWT (HS256) → перевіряємо локально
    logger.info("get_current_identity: treating token as local JWT (HS256)")
    try:
        payload = decode_access_token(token)
    except TokenDecodeError as e:
        logger.warning("get_current_identity: local JWT decode failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not found in token",
        )

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    token = creds.credentials
    claims = verify_auth0_token(token)  # тут ми вже очікуємо RS256
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email claim not found"
        )
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
    identity: dict = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
):
    user_id = identity.get("sub")
    if not user_id:
        raise TokenInvalid("Invalid token payload")
    user = await user_repo.get_by_id(db, int(user_id))
    if not user:
        raise NotFound("User not found")
    return user


# async def get_current_user_auth0(
#     creds: HTTPAuthorizationCredentials | None = Depends(bearer),
#     db: AsyncSession = Depends(get_db),
# ):
#     if creds is None or creds.scheme.lower() != "bearer":
#         logger.info("No credentials provided")
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
#
#     logger.info("Auth header scheme=%s", getattr(creds, "scheme", None))
#
#     token = creds.credentials
#     logger.info("Got bearer token with length=%s", len(token) if token else 0)
#
#     try:
#         claims = verify_auth0_token(token)
#         logger.info("verify_auth0_token OK: sub=%s aud=%s iss=%s",
#                  claims.get("sub"), claims.get("aud"), claims.get("iss"))
#         return {
#             "source": "auth0",
#             "email": extract_email(claims),
#             "payload": claims,
#         }
#     except Exception as e:
#         # важливо: зловили і залогували ПЕРЕД тим як віддати 401
#         logger.exception("verify_auth0_token FAILED: %s", e)
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
#
#
#     payload = verify_auth0_token(creds.credentials)
#     email = extract_email(payload)
#     if not email:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email claim not found")
#
#     user = await user_repo.get_by_email(db, email)
#     if not user:
#         # автостворення лайт-юзера
#         user = await user_repo.create(
#             db,
#             email=email,
#             full_name=None,
#             hashed_password="",
#         )
#     return user
