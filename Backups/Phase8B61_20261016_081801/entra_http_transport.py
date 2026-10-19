"""Bounded HTTPS JSON transport for trusted identity metadata.

This module is intentionally not wired into production authentication.
Only fixed, caller-approved hosts may be contacted. Redirects are disabled.
"""

from __future__ import annotations

import json
from typing import Any, Callable
from urllib.parse import urlparse

import httpx

from app.entra_metadata_client import MetadataTrustError


DEFAULT_MAX_RESPONSE_BYTES = 1_048_576


def fetch_json_document(
    url: str,
    *,
    trusted_hosts: set[str],
    timeout_seconds: float = 3.0,
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    client_factory: Callable[..., Any] = httpx.Client,
) -> dict[str, Any]:
    """Fetch a bounded JSON object from an approved HTTPS host.

    TLS verification remains enabled. Environment proxy configuration is not
    inherited. Redirects are rejected rather than followed. The caller must
    supply a fixed, approved metadata URL, never a URL from a token.
    """
    if not isinstance(url, str) or not url.strip():
        raise MetadataTrustError("Request URL must be a non-empty string")

    parsed = urlparse(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise MetadataTrustError("Request URL must use HTTPS and include a hostname")
    if parsed.username or parsed.password or parsed.fragment:
        raise MetadataTrustError("Request URL credentials and fragments are not allowed")

    if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool):
        raise MetadataTrustError("Timeout must be numeric")
    if not 0 < timeout_seconds <= 10:
        raise MetadataTrustError("Timeout must be greater than 0 and at most 10 seconds")

    if not isinstance(max_response_bytes, int) or isinstance(max_response_bytes, bool):
        raise MetadataTrustError("Response-size limit must be an integer")
    if not 1 <= max_response_bytes <= 4 * 1024 * 1024:
        raise MetadataTrustError("Response-size limit must be between 1 byte and 4 MiB")

    if not isinstance(trusted_hosts, set) or not trusted_hosts:
        raise MetadataTrustError("Trusted host allowlist must be a non-empty set")

    host = parsed.hostname.lower().rstrip(".")
    allowed = {
        item.lower().rstrip(".")
        for item in trusted_hosts
        if isinstance(item, str) and item.strip()
    }
    if host not in allowed:
        raise MetadataTrustError("Request hostname is not in the approved allowlist")

    try:
        with client_factory(
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=False,
            verify=True,
            trust_env=False,
        ) as client:
            with client.stream("GET", url, headers={"Accept": "application/json"}) as response:
                if response.status_code != 200:
                    raise MetadataTrustError(
                        f"Metadata endpoint returned unexpected HTTP status {response.status_code}"
                    )

                content_type = response.headers.get("content-type", "")
                media_type = content_type.split(";", 1)[0].strip().lower()
                if media_type != "application/json" and not (
                    media_type.startswith("application/") and media_type.endswith("+json")
                ):
                    raise MetadataTrustError("Metadata endpoint did not return JSON content")

                declared_length = response.headers.get("content-length")
                if declared_length is not None:
                    try:
                        length = int(declared_length)
                    except (TypeError, ValueError) as exc:
                        raise MetadataTrustError("Invalid response Content-Length") from exc
                    if length < 0 or length > max_response_bytes:
                        raise MetadataTrustError("Metadata response exceeds the size limit")

                chunks: list[bytes] = []
                total = 0
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > max_response_bytes:
                        raise MetadataTrustError("Metadata response exceeds the size limit")
                    chunks.append(chunk)

                raw = b"".join(chunks)

    except MetadataTrustError:
        raise
    except httpx.HTTPError as exc:
        raise MetadataTrustError("Trusted metadata HTTPS request failed") from exc
    except (OSError, TimeoutError) as exc:
        raise MetadataTrustError("Trusted metadata transport failed") from exc

    try:
        document = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MetadataTrustError("Metadata response is not valid JSON") from exc

    if not isinstance(document, dict):
        raise MetadataTrustError("Metadata response must be a JSON object")

    return document
