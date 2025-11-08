from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any, Dict, Optional
from datetime import datetime, timedelta, timezone

import httpx

from fastapi import HTTPException, status
import jwt
from jwt import PyJWKClient, InvalidTokenError, decode

from app.core.config import settings

# Простенький in-memory кеш JWKS
_JWKS: Optional[Dict[str, Any]] = None
_JWKS_EXPIRES_AT: Optional[datetime] = None

JWKS_URL = f"https://{settings.auth0.DOMAIN}/.well-known/jwks.json"
logging.info(F"JWKS_URL ={JWKS_URL}")
ISSUER = settings.auth0.ISSUER
logging.info(F"ISSUER ={ISSUER}")
AUDIENCE = settings.auth0.AUDIENCE
logging.info(F"AUDIENCE ={AUDIENCE}")

def _jwks_url() -> str:
    """
    Будує URL до JWKS. Безпечно використовувати ISSUER (із завершаючим '/').
    """
    issuer = settings.auth0.ISSUER
    if not issuer.endswith("/"):
        issuer += "/"
    return f"{issuer}.well-known/jwks.json"

def get_jwks(force: bool = False) -> Dict[str, Any]:
    """
    Отримує JWKS з кешем (за замовчуванням 10 хв). Синхронний варіант.
    """
    global _JWKS, _JWKS_EXPIRES_AT

    now = datetime.now(tz=timezone.utc)
    if (not force) and _JWKS is not None and _JWKS_EXPIRES_AT and now < _JWKS_EXPIRES_AT:
        return _JWKS

    url = _jwks_url()
    timeout = httpx.Timeout(5.0, connect=5.0)
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        # Якщо мережа впала, але є старий кеш – віддаємо його.
        if _JWKS is not None:
            return _JWKS
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch JWKS")

    if not isinstance(data, dict) or "keys" not in data:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid JWKS payload")

    _JWKS = data
    ttl = max(30, int(settings.auth0.JWKS_CACHE_SECONDS or 600))
    _JWKS_EXPIRES_AT = now + timedelta(seconds=ttl)
    return _JWKS

def _pick_jwk_for_token(token: str) -> Dict[str, Any]:
    """
    Дістає kid з заголовка токена та підбирає відповідний JWK із кешованого JWKS.
    """
    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header")

    kid = header.get("kid")
    if not kid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing kid in token header")

    jwks = get_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    # Якщо ключ не знайдено – можливо, JWKS оновився, спробуємо refetch
    jwks = get_jwks(force=True)
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signing key not found")

def _public_key_from_jwk(jwk_dict: Dict[str, Any]):
    """
    Конвертує JWK у RSA публічний ключ (об'єкт cryptography), який приймає PyJWT.
    """
    try:
        jwk_json = json.dumps(jwk_dict)
        return jwt.algorithms.RSAAlgorithm.from_jwk(jwk_json)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWK")


@lru_cache(maxsize=1)
def _jwks_client_cached() -> PyJWKClient:
    # PyJWKClient сам фетчить JWKS та кешує всередині
    return PyJWKClient(JWKS_URL)


def extract_email(payload: Dict[str, Any]) -> Optional[str]:
    claim = settings.auth0.EMAIL_CLAIM
    return payload.get("email") or payload.get(claim)


@lru_cache(maxsize=1)
def get_jwks_client() -> PyJWKClient:
    return PyJWKClient(JWKS_URL)


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    return PyJWKClient(JWKS_URL)


def verify_auth0_token(token: str) -> Dict[str, Any]:
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token).key
        payload = decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=AUDIENCE,
            issuer=ISSUER,
        )
        return payload
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        ) from e
