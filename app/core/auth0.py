from loguru import logger
from functools import lru_cache
from urllib.parse import urljoin

import jwt

try:
    from jwt import PyJWKClient  # PyJWT 2.x
except ImportError:               # деякі старі оточення
    from jwt.jwks_client import PyJWKClient


from app.core.config import settings  # звідки ти читаєш AUTH0_* значення






def _jwks_url() -> str:
    """
    Будуємо правильний JWKS URL з урахуванням слеша в кінці ISSUER.
    Приклад: https://tenant.us.auth0.com/.well-known/jwks.json
    """
    issuer = settings.auth0.ISSUER  # має закінчуватись на "/"
    logger.info("Issuer: %s", issuer)
    # urljoin сам розрулить зайві/відсутні слеші
    return urljoin(issuer, ".well-known/jwks.json")


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    url = getattr(settings.auth0, "JWKS_URL", None) or _jwks_url()
    logger.info("Auth0 PyJWKClient init: {}", url)
    return PyJWKClient(url)


def verify_auth0_token(token: str) -> dict:
    # необов'язково, але корисно для діагностики
    try:
        unverified = jwt.get_unverified_header(token)
        logger.info("AUTH0 token header: {}", (unverified.get("kid"), unverified.get("alg")))
    except Exception as e:
        logger.exception("Failed to parse JWT header: %s", e)
        raise

    logger.info(
        "AUTH0 using: ISS=%s AUD=%s JWKS=%s",
        settings.auth0.ISSUER,
        settings.auth0.AUDIENCE,
        getattr(settings.auth0, "JWKS_URL", None) or _jwks_url(),
    )

    signing_key = _jwks_client().get_signing_key_from_jwt(token).key
    payload = jwt.decode(
        token,
        signing_key,
        algorithms=["RS256"],
        audience=settings.auth0.AUDIENCE,
        issuer=settings.auth0.ISSUER,
    )
    logger.info("AUTH0 payload OK: sub=%s", payload.get("sub"))
    return payload


def extract_email(payload: dict) -> str | None:
    # шукаємо кастомний клейм або стандартний email
    email_claim = getattr(settings.auth0, "EMAIL_CLAIM", None)
    return payload.get(email_claim) or payload.get("email")
