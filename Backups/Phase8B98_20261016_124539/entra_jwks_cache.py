"""Bounded in-memory JWKS cache with explicit refresh.

The loader is injected by the caller. This module performs no network
requests and is not wired into production authentication.

Expired keys are never returned by get(). A failed refresh does not
extend the previous expiry time. Callers must provide trusted loading
and transport logic before using this cache in an application.
"""

from __future__ import annotations

from copy import deepcopy
from threading import RLock
from time import monotonic
from typing import Any, Callable

from app.entra_metadata_client import (
    MetadataTrustError,
    validate_jwks_document,
)


class JWKSCacheError(RuntimeError):
    """Raised when trusted JWKS data cannot be loaded or validated."""


class JWKSCache:
    """Thread-safe in-memory JWKS cache with bounded TTL."""

    def __init__(
        self,
        loader: Callable[[], Any],
        *,
        ttl_seconds: float = 300.0,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if not callable(loader):
            raise ValueError("loader must be callable")
        if not isinstance(ttl_seconds, (int, float)) or isinstance(
            ttl_seconds, bool
        ):
            raise ValueError("ttl_seconds must be numeric")
        if not 0 < ttl_seconds <= 3600:
            raise ValueError("ttl_seconds must be greater than 0 and at most 3600")
        if not callable(clock):
            raise ValueError("clock must be callable")

        self._loader = loader
        self._ttl_seconds = float(ttl_seconds)
        self._clock = clock
        self._lock = RLock()
        self._document: dict[str, Any] | None = None
        self._expires_at: float | None = None

    def _load_and_validate(self) -> dict[str, Any]:
        try:
            document = self._loader()
            validated = validate_jwks_document(document)
            # Never expose the loader's mutable object to the cache.
            return deepcopy(validated)
        except (MetadataTrustError, TypeError, ValueError) as exc:
            raise JWKSCacheError("Loaded JWKS failed validation") from exc
        except Exception as exc:
            raise JWKSCacheError("JWKS loader failed") from exc

    def get(self) -> dict[str, Any]:
        """Return a copy of cached keys, loading only when missing/expired."""
        with self._lock:
            now = self._clock()

            if (
                self._document is not None
                and self._expires_at is not None
                and now < self._expires_at
            ):
                return deepcopy(self._document)

            # Do not return expired keys if the loader fails.
            document = self._load_and_validate()
            self._document = document
            self._expires_at = self._clock() + self._ttl_seconds
            return deepcopy(document)

    def refresh(self) -> dict[str, Any]:
        """Force a fresh load and replace the cache only after validation."""
        with self._lock:
            document = self._load_and_validate()
            self._document = document
            self._expires_at = self._clock() + self._ttl_seconds
            return deepcopy(document)

    def invalidate(self) -> None:
        """Discard cached keys so the next get() must reload."""
        with self._lock:
            self._document = None
            self._expires_at = None

    @property
    def is_valid(self) -> bool:
        """Whether a non-expired cache entry currently exists."""
        with self._lock:
            return (
                self._document is not None
                and self._expires_at is not None
                and self._clock() < self._expires_at
            )