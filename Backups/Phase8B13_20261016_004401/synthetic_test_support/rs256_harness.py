"""TEST-ONLY RS256 harness; never use for application authentication."""
import base64
import hashlib
import hmac
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding


class SyntheticRS256Error(ValueError):
    pass


def _enc(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _dec(value: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise SyntheticRS256Error("Malformed base64url value.")
    try:
        raw = value.encode("ascii")
        padded = raw + b"=" * ((4 - len(raw) % 4) % 4)
        return base64.b64decode(padded, altchars=b"-_", validate=True)
    except Exception as exc:
        raise SyntheticRS256Error("Malformed base64url value.") from exc


def issue_rs256_token(claims: dict, *, kid: str, private_key) -> str:
    if not isinstance(claims, dict) or not kid:
        raise ValueError("Claims dictionary and key ID are required.")
    header = {"alg": "RS256", "typ": "JWT", "kid": kid}
    h = _enc(json.dumps(header, separators=(",", ":"), sort_keys=True).encode())
    p = _enc(json.dumps(claims, separators=(",", ":"), sort_keys=True).encode())
    signing_input = f"{h}.{p}".encode("ascii")
    signature = private_key.sign(
        signing_input, padding.PKCS1v15(), hashes.SHA256()
    )
    return f"{h}.{p}.{_enc(signature)}"


def verify_rs256_token(
    token: str,
    *,
    public_keys_by_kid: dict,
    expected_issuer: str,
    expected_audience: str,
    now: float,
) -> dict:
    """Verify test RS256 signature and core claims using supplied trusted keys."""
    if not isinstance(token, str):
        raise SyntheticRS256Error("Malformed token.")
    parts = token.split(".")
    if len(parts) != 3:
        raise SyntheticRS256Error("Malformed token.")

    try:
        header = json.loads(_dec(parts[0]))
        claims = json.loads(_dec(parts[1]))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SyntheticRS256Error("Malformed token JSON.") from exc

    if not isinstance(header, dict) or not isinstance(claims, dict):
        raise SyntheticRS256Error("Malformed token objects.")
    if header.get("alg") != "RS256":
        raise SyntheticRS256Error("Disallowed algorithm.")

    kid = header.get("kid")
    if not isinstance(kid, str) or kid not in public_keys_by_kid:
        raise SyntheticRS256Error("Unknown signing key.")

    try:
        public_keys_by_kid[kid].verify(
            _dec(parts[2]),
            f"{parts[0]}.{parts[1]}".encode("ascii"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise SyntheticRS256Error("Invalid signature.") from exc

    if claims.get("iss") != expected_issuer:
        raise SyntheticRS256Error("Wrong issuer.")

    aud = claims.get("aud")
    audiences = [aud] if isinstance(aud, str) else aud
    if not isinstance(audiences, list) or not all(
        isinstance(item, str) for item in audiences
    ):
        raise SyntheticRS256Error("Malformed audience.")
    if expected_audience not in audiences:
        raise SyntheticRS256Error("Wrong audience.")

    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub.strip():
        raise SyntheticRS256Error("Missing subject.")

    exp = claims.get("exp")
    if isinstance(exp, bool) or not isinstance(exp, (int, float)):
        raise SyntheticRS256Error("Invalid expiry.")
    if exp <= now:
        raise SyntheticRS256Error("Expired token.")

    if "nbf" in claims:
        nbf = claims["nbf"]
        if isinstance(nbf, bool) or not isinstance(nbf, (int, float)):
            raise SyntheticRS256Error("Invalid not-before claim.")
        if nbf > now:
            raise SyntheticRS256Error("Token not yet valid.")

    return dict(claims)
