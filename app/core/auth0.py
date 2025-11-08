from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any, Dict, Optional
from datetime import datetime, timedelta, timezone

import httpx

from fastapi import HTTPException, status
import jwt
from jwt import PyJWKClient, InvalidTokenError
from jwt.algorithms import RSAAlgorithm

from app.core.config import settings


_JWKS: Optional[Dict[str, Any]] = None
_JWKS_EXPIRES_AT: Optional[datetime] = None

JWKS_URL = f"https://{settings.auth0.DOMAIN}/.well-known/jwks.json"
logging.info(F"JWKS_URL ={JWKS_URL}")
ISSUER = settings.auth0.ISSUER
logging.info(F"ISSUER ={ISSUER}")
AUDIENCE = settings.auth0.AUDIENCE
logging.info(F"AUDIENCE ={AUDIENCE}")


def _jwks_url() -> str:
    issuer = settings.auth0.ISSUER
    if not issuer.endswith("/"):
        issuer += "/"
    return f"{issuer}.well-known/jwks.json"


def get_jwks(force: bool = False) -> Dict[str, Any]:
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
        if _JWKS is not None:
            return _JWKS
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch JWKS"
        )

    if not isinstance(data, dict) or "keys" not in data:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid JWKS payload"
        )

    _JWKS = data
    ttl = max(30, int(settings.auth0.JWKS_CACHE_SECONDS or 600))
    _JWKS_EXPIRES_AT = now + timedelta(seconds=ttl)
    return _JWKS


def _pick_jwk_for_token(token: str) -> Dict[str, Any]:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header"
        )

    kid = header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing kid in token header"
        )

    jwks = get_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    jwks = get_jwks(force=True)
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Signing key not found"
    )


def _public_key_from_jwk(jwk_dict: Dict[str, Any]):
    try:
        jwk_json = json.dumps(jwk_dict)
        return jwt.algorithms.RSAAlgorithm.from_jwk(jwk_json)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWK"
        )


@lru_cache(maxsize=1)
def _jwks_client_cached() -> PyJWKClient:
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


def _find_key_by_kid(jwks: dict, kid: str | None) -> dict | None:
    if not jwks or "keys" not in jwks:
        return None
    for key in jwks["keys"]:
        if key.get("kid") == kid:
            return key
    return None


def verify_auth0_token(token: str) -> dict:
    try:
        header = jwt.get_unverified_header(token)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header"
        )

    kid = header.get("kid")
    jwks = get_jwks()
    key_dict = _find_key_by_kid(jwks, kid)
    if not key_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown key id (kid)"
        )

    public_key = RSAAlgorithm.from_jwk(json.dumps(key_dict))

    try:
        payload = jwt.decode(
            token,
            key=public_key,
            algorithms=[settings.auth0.ALG],
            audience=settings.auth0.AUDIENCE,
            issuer=settings.auth0.ISSUER,
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {e}"
        )

    return payload
