import json
import jwt
import pytest
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric import rsa

from app.core import auth0 as auth0_mod
from app.core.config import settings

from jwt.algorithms import RSAAlgorithm


@pytest.mark.anyio
async def test_verify_auth0_token_ok(monkeypatch):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    jwk_public_json = RSAAlgorithm.to_jwk(public_key)
    jwk_public = json.loads(jwk_public_json)
    kid = "test-kid-123"
    jwk_public.update({"kid": kid, "use": "sig", "alg": "RS256"})

    def fake_get_jwks():
        return {"keys": [jwk_public]}
    monkeypatch.setattr(auth0_mod, "get_jwks", fake_get_jwks, raising=True)

    issuer = "https://example-issuer/"
    audience = "https://be-1.api"
    email_claim = "https://be-1-api/email"

    settings.auth0.ISSUER = issuer
    settings.auth0.AUDIENCE = audience
    settings.auth0.EMAIL_CLAIM = email_claim
    settings.auth0.ALG = "RS256"

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
        headers={"kid": kid},
    )

    decoded = auth0_mod.verify_auth0_token(token)

    assert decoded["sub"] == "google-oauth2|user123"
    assert decoded["iss"] == issuer
    assert audience in decoded["aud"]
    assert decoded[email_claim] == "unit_user@example.com"
