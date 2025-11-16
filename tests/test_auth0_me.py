from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from loguru import logger

from app.core import auth0 as auth0_mod
from app.core.config import settings

AUTH_BASE = "/api/v1/auth"


@pytest.mark.anyio
async def test_auth0_me_ok(client, monkeypatch):
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
    email = "int_user@example.com"
    payload = {
        "iss": issuer,
        "aud": [audience, "https://dev-h21k1w78osfzuvra.us.auth0.com/userinfo"],
        "sub": "google-oauth2|1087-test-int",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "scope": "openid profile email",
        email_claim: email,
    }

    token = jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
        headers={"kid": "int-kid-456"},
    )

    res = await client.get(
        f"{AUTH_BASE}/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    logger.info("BODY: {}", body)

    assert body["email"] == email
    assert isinstance(body["id"], int)
    assert body["full_name"] is None
    assert "created_at" in body
    assert "updated_at" in body
