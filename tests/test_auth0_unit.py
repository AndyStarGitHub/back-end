from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core import auth0 as auth0_mod
from app.core.config import settings


@pytest.mark.anyio
async def test_verify_auth0_token_ok(monkeypatch):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    class FakeKey:
        def __init__(self, key):
            self.key = key

    class FakeClient:
        def get_signing_key_from_jwt(self, token: str):
            return FakeKey(public_key)

    monkeypatch.setattr(
        auth0_mod,
        "_jwks_client",
        lambda: FakeClient(),
        raising=True
    )

    issuer = "https://example-issuer/"
    audience = "https://be-1.api"
    email_claim = "https://be-1-api/email"

    settings.auth0.ISSUER = issuer
    settings.auth0.AUDIENCE = audience
    settings.auth0.EMAIL_CLAIM = email_claim

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

    decoded = auth0_mod.verify_auth0_token(token)

    assert decoded["sub"] == payload["sub"]
    assert decoded[email_claim] == payload[email_claim]
