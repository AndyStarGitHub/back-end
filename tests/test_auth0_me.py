import json
import jwt
import pytest
from datetime import datetime, timedelta, timezone
from jwt.algorithms import RSAAlgorithm
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core import auth0 as auth0_mod
from app.core.config import settings


@pytest.mark.anyio
async def test_auth0_me_ok(client, monkeypatch):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    jwk_public = json.loads(RSAAlgorithm.to_jwk(public_key))
    kid = "int-kid-456"
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
        "sub": "google-oauth2|1087-test-int",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "scope": "openid profile email",
        email_claim: "int_user@example.com",
    }

    token = jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": kid})

    res = await client.get(
        "/api/v1/auth0/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["email"] == "int_user@example.com"
    assert body["sub"] == "google-oauth2|1087-test-int"
    assert body["iss"] == issuer
    assert audience in body["aud"]
