from loguru import logger
from functools import lru_cache
from urllib.parse import urljoin

import jwt

try:
    from jwt import PyJWKClient
except ImportError:
    from jwt.jwks_client import PyJWKClient


from app.core.config import settings


def _jwks_url() -> str:
    issuer = settings.auth0.ISSUER
    logger.info("Issuer: {}", issuer)
    return urljoin(issuer, ".well-known/jwks.json")


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    url = getattr(settings.auth0, "JWKS_URL", None) or _jwks_url()
    logger.info("Auth0 PyJWKClient init: {}", url)
    return PyJWKClient(url)


def verify_auth0_token(token: str) -> dict:
    try:
        unverified = jwt.get_unverified_header(token)
        logger.info(
            "AUTH0 token header: {}",
            (unverified.get("kid"), unverified.get("alg"))
        )
    except Exception as e:
        logger.exception("Failed to parse JWT header: {}}", e)
        raise

    logger.info("AUTH0 using issuer {}:",   settings.auth0.ISSUER)
    logger.info("AUTH0 using audience {}:",   settings.auth0.AUDIENCE)
    logger.info(
        "AUTH0 using JWKS {}:",
        getattr(settings.auth0, "JWKS_URL", None) or _jwks_url())

    signing_key = _jwks_client().get_signing_key_from_jwt(token).key
    logger.info("verify_auth0_token - signing_key {}:",   signing_key)
    payload = jwt.decode(
        token,
        signing_key,
        algorithms=["RS256"],
        audience=settings.auth0.AUDIENCE,
        issuer=settings.auth0.ISSUER,
    )
    logger.info("verify_auth0_token - payload {}:",   payload)
    logger.info("AUTH0 payload OK sub: {}", payload.get("sub"))
    logger.info("AUTH0 payload : {}", payload)
    return payload


def extract_email(payload: dict) -> str | None:
    email_claim = getattr(settings.auth0, "EMAIL_CLAIM", None)
    return payload.get(email_claim) or payload.get("email")
