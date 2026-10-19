"""TEST-ONLY synthetic JWT harness.

This module is isolated from application authentication.
It uses HS256 and locally supplied synthetic keys to test JWT-like
validation behavior. It is NOT a production OIDC verifier.

Do not use this module to authenticate application users.
"""
import base64
import hashlib
import hmac
import json
import time


class SyntheticTokenError(ValueError):
    pass


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise SyntheticTokenError("Malformed base64url value.")
    try:
        padded = value + ("=" * ((4 - len(value) % 4) % 4))
        return base64.b64decode(
            padded.encode("ascii"), altchars=b"-_", validate=True
        )
    except Exception as exc:
        raise SyntheticTokenError("Malformed base64url value.") from exc


def issue_synthetic_token(claims: dict, *, kid: str, key: bytes) -> str:
    if not isinstance(claims, dict):
        raise ValueError("Claims must be a dictionary.")
    if not kid or not isinstance(key, bytes) or len(key) < 32:
        raise ValueError("Use a key ID and at least 32 synthetic key bytes.")

    header = {"alg": "HS256", "typ": "JWT", "kid": kid}
    encoded_header = _b64encode(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode()
    )
    encoded_claims = _b64encode(
        json.dumps(claims, separators=(",", ":"), sort_keys=True).encode()
    )
    signing_input = f"{encoded_header}.{encoded_claims}".encode("ascii")
    signature = hmac.new(key, signing_input, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_claims}.{_b64encode(signature)}"


def verify_synthetic_token(
    token: str,
    *,
    keys_by_kid: dict[str, bytes],
    expected_issuer: str,
    expected_audience: str,
    now: float | None = None,
) -> dict:
    """Verify a synthetic HS256 token with an explicitly supplied test key set."""
    if not isinstance(token, str):
        raise SyntheticTokenError("Token must be a string.")

    parts = token.split(".")
    if len(parts) != 3:
        raise SyntheticTokenError("Malformed token.")

    try:
        header = json.loads(_b64decode(parts[0]))
        claims = json.loads(_b64decode(parts[1]))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SyntheticTokenError("Malformed token JSON.") from exc

    if not isinstance(header, dict) or not isinstance(claims, dict):
        raise SyntheticTokenError("Token header and claims must be objects.")

    # Algorithm is fixed. Never trust the token to choose the verifier.
    if header.get("alg") != "HS256":
        raise SyntheticTokenError("Disallowed algorithm.")

    kid = header.get("kid")
    if not isinstance(kid, str) or kid not in keys_by_kid:
        raise SyntheticTokenError("Unknown signing key.")

    key = keys_by_kid[kid]
    if not isinstance(key, bytes) or len(key) < 32:
        raise SyntheticTokenError("Invalid configured test key.")

    signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
    supplied_signature = _b64decode(parts[2])
    expected_signature = hmac.new(key, signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(supplied_signature, expected_signature):
        raise SyntheticTokenError("Invalid signature.")

    if claims.get("iss") != expected_issuer:
        raise SyntheticTokenError("Wrong issuer.")

    audience = claims.get("aud")
    if isinstance(audience, str):
        audiences = [audience]
    elif isinstance(audience, list) and all(
        isinstance(item, str) for item in audience
    ):
        audiences = audience
    else:
        raise SyntheticTokenError("Malformed audience.")

    if expected_audience not in audiences:
        raise SyntheticTokenError("Wrong audience.")

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise SyntheticTokenError("Missing subject.")

    expiry = claims.get("exp")
    if isinstance(expiry, bool) or not isinstance(expiry, (int, float)):
        raise SyntheticTokenError("Missing or invalid expiry.")

    current_time = time.time() if now is None else now
    if expiry <= current_time:
        raise SyntheticTokenError("Expired token.")

    if "nbf" in claims:
        not_before = claims["nbf"]
        if (
            isinstance(not_before, bool)
            or not isinstance(not_before, (int, float))
        ):
            raise SyntheticTokenError("Invalid not-before claim.")
        if not_before > current_time:
            raise SyntheticTokenError("Token not yet valid.")

    return dict(claims)
