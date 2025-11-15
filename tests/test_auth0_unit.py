# tests/test_auth0_unit.py
import json
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from app.core import auth0 as auth0_mod
from app.core.config import settings


@pytest.mark.anyio
async def test_verify_auth0_token_ok(monkeypatch):
    # 1) Генеруємо пару ключів
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    # 2) Фейковий PyJWKClient
    class FakeKey:
        def __init__(self, key):
            self.key = key

    class FakeClient:
        def get_signing_key_from_jwt(self, token: str):
            # Для будь-якого токена завжди повертаємо наш публічний ключ
            return FakeKey(public_key)

    # підміняємо _jwks_client у auth0-модулі
    monkeypatch.setattr(auth0_mod, "_jwks_client", lambda: FakeClient(), raising=True)

    # 3) Налаштування
    issuer = "https://example-issuer/"
    audience = "https://be-1.api"
    email_claim = "https://be-1-api/email"

    settings.auth0.ISSUER = issuer
    settings.auth0.AUDIENCE = audience
    settings.auth0.EMAIL_CLAIM = email_claim

    # 4) Формуємо токен RS256 з тим же ключем
    now = datetime.now(timezone.utc)
    payload = {
        "iss": issuer,
        "aud": [audience, "https://dev-h21k1w78osfzuvra.us.auth0.com/userinfo"],
        "sub": "google-oauth2|user123",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "scope": "openid profile email",
        email_claim: "unit_user@example.com",
    }

    token = jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
        headers={"kid": "test-kid-123"},
    )

    # 5) Виклик функції
    decoded = auth0_mod.verify_auth0_token(token)

    assert decoded["sub"] == payload["sub"]
    assert decoded[email_claim] == payload[email_claim]
