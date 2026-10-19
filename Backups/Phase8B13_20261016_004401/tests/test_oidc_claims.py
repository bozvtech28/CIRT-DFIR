import pytest

from app.oidc_claims import InvalidOIDCClaims, validate_verified_claims


ISSUER = "https://identity.example.invalid/"
AUDIENCE = "cirt-dfir-api"
NOW = 1_800_000_000


def valid_claims():
    return {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "synthetic-user-001",
        "exp": NOW + 300,
    }


def test_accepts_valid_verified_claims():
    result = validate_verified_claims(
        valid_claims(),
        expected_issuer=ISSUER,
        expected_audience=AUDIENCE,
        now=NOW,
    )
    assert result["sub"] == "synthetic-user-001"


def test_rejects_expired_token_claims():
    claims = valid_claims()
    claims["exp"] = NOW - 1
    with pytest.raises(InvalidOIDCClaims, match="expired"):
        validate_verified_claims(
            claims,
            expected_issuer=ISSUER,
            expected_audience=AUDIENCE,
            now=NOW,
        )


def test_rejects_wrong_issuer():
    claims = valid_claims()
    claims["iss"] = "https://unapproved.example.invalid/"
    with pytest.raises(InvalidOIDCClaims, match="issuer"):
        validate_verified_claims(
            claims,
            expected_issuer=ISSUER,
            expected_audience=AUDIENCE,
            now=NOW,
        )


def test_rejects_wrong_audience():
    claims = valid_claims()
    claims["aud"] = "another-api"
    with pytest.raises(InvalidOIDCClaims, match="audience"):
        validate_verified_claims(
            claims,
            expected_issuer=ISSUER,
            expected_audience=AUDIENCE,
            now=NOW,
        )


def test_accepts_expected_audience_in_audience_list():
    claims = valid_claims()
    claims["aud"] = ["another-api", AUDIENCE]
    validate_verified_claims(
        claims,
        expected_issuer=ISSUER,
        expected_audience=AUDIENCE,
        now=NOW,
    )


def test_rejects_missing_subject():
    claims = valid_claims()
    claims.pop("sub")
    with pytest.raises(InvalidOIDCClaims, match="subject"):
        validate_verified_claims(
            claims,
            expected_issuer=ISSUER,
            expected_audience=AUDIENCE,
            now=NOW,
        )


def test_rejects_future_not_before_claim():
    claims = valid_claims()
    claims["nbf"] = NOW + 60
    with pytest.raises(InvalidOIDCClaims, match="not yet valid"):
        validate_verified_claims(
            claims,
            expected_issuer=ISSUER,
            expected_audience=AUDIENCE,
            now=NOW,
        )


def test_rejects_missing_expiry():
    claims = valid_claims()
    claims.pop("exp")
    with pytest.raises(InvalidOIDCClaims, match="expiry"):
        validate_verified_claims(
            claims,
            expected_issuer=ISSUER,
            expected_audience=AUDIENCE,
            now=NOW,
        )
