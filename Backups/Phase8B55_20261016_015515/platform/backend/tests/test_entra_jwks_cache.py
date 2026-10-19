import pytest

from app.entra_jwks_cache import JWKSCache, JWKSCacheError


def make_jwks(kid="synthetic-key-1"):
    return {
        "keys": [
            {
                "kid": kid,
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "n": "synthetic-modulus-" + kid,
                "e": "AQAB",
            }
        ]
    }


class FakeClock:
    def __init__(self, start=100.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def test_first_get_loads_and_caches_document():
    calls = []
    source = make_jwks()

    def loader():
        calls.append(1)
        return source

    cache = JWKSCache(loader, ttl_seconds=30)
    assert cache.get() == source
    assert cache.get() == source
    assert len(calls) == 1
    assert cache.is_valid


def test_cache_expires_at_ttl_boundary():
    clock = FakeClock()
    calls = []

    def loader():
        calls.append(1)
        return make_jwks()

    cache = JWKSCache(loader, ttl_seconds=10, clock=clock)
    cache.get()
    clock.advance(9.99)
    cache.get()
    assert len(calls) == 1

    clock.advance(0.01)
    cache.get()
    assert len(calls) == 2


def test_expired_entry_is_reloaded():
    clock = FakeClock()
    calls = []

    def loader():
        calls.append(1)
        return make_jwks(f"synthetic-key-{len(calls)}")

    cache = JWKSCache(loader, ttl_seconds=5, clock=clock)
    assert cache.get()["keys"][0]["kid"] == "synthetic-key-1"

    clock.advance(6)
    assert cache.get()["keys"][0]["kid"] == "synthetic-key-2"


def test_refresh_replaces_keys_after_rotation():
    current = {"value": make_jwks("synthetic-old-key")}

    cache = JWKSCache(lambda: current["value"])
    assert cache.get()["keys"][0]["kid"] == "synthetic-old-key"

    current["value"] = make_jwks("synthetic-new-key")
    refreshed = cache.refresh()

    assert refreshed["keys"][0]["kid"] == "synthetic-new-key"
    assert cache.get()["keys"][0]["kid"] == "synthetic-new-key"


def test_invalidate_forces_next_load():
    calls = []

    def loader():
        calls.append(1)
        return make_jwks()

    cache = JWKSCache(loader)
    cache.get()
    cache.invalidate()

    assert not cache.is_valid
    cache.get()
    assert len(calls) == 2


def test_mutating_returned_document_does_not_mutate_cache():
    cache = JWKSCache(lambda: make_jwks())
    first = cache.get()
    first["keys"][0]["kid"] = "tampered"

    second = cache.get()
    assert second["keys"][0]["kid"] == "synthetic-key-1"


def test_mutating_loader_source_does_not_mutate_cache():
    source = make_jwks()
    cache = JWKSCache(lambda: source)
    cache.get()

    source["keys"][0]["kid"] = "tampered"
    assert cache.get()["keys"][0]["kid"] == "synthetic-key-1"


def test_expired_keys_not_returned_if_loader_fails():
    clock = FakeClock()
    state = {"fail": False}

    def loader():
        if state["fail"]:
            raise OSError("synthetic loader failure")
        return make_jwks()

    cache = JWKSCache(loader, ttl_seconds=2, clock=clock)
    cache.get()

    clock.advance(3)
    state["fail"] = True

    with pytest.raises(JWKSCacheError):
        cache.get()

    assert not cache.is_valid


def test_invalid_refresh_does_not_replace_valid_unexpired_cache():
    state = {"document": make_jwks("synthetic-original")}

    def loader():
        return state["document"]

    cache = JWKSCache(loader, ttl_seconds=30)
    cache.get()

    state["document"] = {"keys": []}
    with pytest.raises(JWKSCacheError):
        cache.refresh()

    # The previous entry is still unexpired, but refresh reported failure.
    # It must not be extended by the failed refresh.
    assert cache.get()["keys"][0]["kid"] == "synthetic-original"


@pytest.mark.parametrize("ttl", [0, -1, 3601, True, "5"])
def test_rejects_invalid_ttl(ttl):
    with pytest.raises(ValueError):
        JWKSCache(lambda: make_jwks(), ttl_seconds=ttl)


def test_rejects_non_callable_loader():
    with pytest.raises(ValueError):
        JWKSCache(None)


def test_rejects_non_callable_clock():
    with pytest.raises(ValueError):
        JWKSCache(lambda: make_jwks(), clock=None)


def test_invalid_loaded_jwks_is_rejected():
    cache = JWKSCache(lambda: {"keys": []})
    with pytest.raises(JWKSCacheError):
        cache.get()


def test_loader_exception_is_wrapped():
    def loader():
        raise OSError("synthetic transport failure")

    cache = JWKSCache(loader)
    with pytest.raises(JWKSCacheError):
        cache.get()


def test_refresh_loads_even_when_cache_is_valid():
    calls = []

    def loader():
        calls.append(1)
        return make_jwks(f"synthetic-key-{len(calls)}")

    cache = JWKSCache(loader)
    assert cache.get()["keys"][0]["kid"] == "synthetic-key-1"
    assert cache.refresh()["keys"][0]["kid"] == "synthetic-key-2"
    assert len(calls) == 2


def test_cache_ttl_is_bounded_to_one_hour():
    with pytest.raises(ValueError):
        JWKSCache(lambda: make_jwks(), ttl_seconds=3600.01)


def test_cache_is_initially_invalid():
    cache = JWKSCache(lambda: make_jwks())
    assert not cache.is_valid


def test_get_returns_a_dict_copy():
    cache = JWKSCache(lambda: make_jwks())
    result = cache.get()
    assert isinstance(result, dict)
    assert result is not cache._document