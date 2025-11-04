import time
from typing import Any, Dict, Optional
from functools import lru_cache

import httpx
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWKError

from app.core.config import settings


JWKS_URL = f"https://{settings.auth0.DOMAIN}/.well-known/jwks.json"
JWKS_CACHE: Dict[str, Any] = {}
JWKS_EXPIRES_AT: float = 0
JWKS_TTL_SECONDS = 60 * 10

@lru_cache(maxsize=1)
def _fetch_jwks() -> Dict[str, Any]:
    with httpx.Client(timeout=5.0) as client:
        r = client.get(JWKS_URL)
        r.raise_for_status()
        return r.json()


def _get_signing_key(kid: str) -> Optional[Dict[str, Any]]:
    jwks = _fetch_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    return None


def verify_auth0_token(token: str) -> Dict[str, Any]:
    """
    Перевіряє RS256 токен від Auth0 через JWKS і повертає payload.
    """
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as e:
        raise ValueError(f"Invalid token header: {e}")

    kid = header.get("kid")
    if not kid:
        raise ValueError("Token header missing 'kid'.")

    key = _get_signing_key(kid)
    if not key:
        # скидаємо кеш JWKS і пробуємо ще раз (ротація ключів)
        _fetch_jwks.cache_clear()  # type: ignore
        key = _get_signing_key(kid)
        if not key:
            raise ValueError("Signing key not found for kid.")

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=[settings.auth0.ALG],
            audience=settings.auth0.AUDIENCE,
            issuer=settings.auth0.ISSUER,
        )
        return payload
    except ExpiredSignatureError:
        raise ValueError("Token expired.")
    except (JWTError, JWKError) as e:
        raise ValueError(f"Token verification failed: {e}")


def _jwks_url() -> str:
    domain = settings.auth0.DOMAIN if hasattr(settings, "auth0") else settings.AUTH0_DOMAIN
    return f"https://{domain}/.well-known/jwks.json"

async def _load_jwks() -> Dict[str, Any]:
    global JWKS_CACHE, JWKS_EXPIRES_AT
    now = time.time()
    if JWKS_CACHE and now < JWKS_EXPIRES_AT:
        return JWKS_CACHE

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(_jwks_url())
        resp.raise_for_status()
        data = resp.json()

    JWKS_CACHE = {j["kid"]: j for j in data.get("keys", [])}
    JWKS_EXPIRES_AT = now + JWKS_TTL_SECONDS
    return JWKS_CACHE

def _build_rsa_key(jwk: Dict[str, str]) -> Dict[str, Any]:
    # python-jose приймає JWK напряму як key; або можна зібрати вручну.
    # Тут достатньо повернути JWK як ключ.
    return jwk

async def verify_auth0_token(token: str) -> Dict[str, Any]:
    """
    Перевіряє RS256 токен від Auth0:
    - валідний підпис (через JWKS),
    - правильні iss / aud,
    - не протермінований.
    Повертає дикт клеймів.
    """
    # 1) дістаємо заголовок, беремо kid
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    if not kid:
        raise ValueError("Missing 'kid' in token header")

    # 2) підвантажуємо JWKS і беремо відповідний ключ
    jwks = await _load_jwks()
    jwk = jwks.get(kid)
    if not jwk:
        # Можливо, ключі оновились: спроба форс-перезавантаження
        JWKS_CACHE.clear()
        jwks = await _load_jwks()
        jwk = jwks.get(kid)
        if not jwk:
            raise ValueError("Signing key not found for kid")

    key = _build_rsa_key(jwk)

    # 3) декодуємо/верифікуємо
    issuer = getattr(settings, "AUTH0_ISSUER", None) or settings.auth0.ISSUER
    audience = getattr(settings, "AUTH0_AUDIENCE", None) or settings.auth0.AUDIENCE

    # невеликий leeway на годинник
    options = {"verify_aud": True}
    claims = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=audience,
        issuer=issuer,
        options=options,
    )
    return claims
