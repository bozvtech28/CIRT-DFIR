from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from time import sleep

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


def test_concurrent_gets_share_one_initial_load():
    counter_lock = Lock()
    calls = []

    def loader():
        with counter_lock:
            calls.append(1)
        sleep(0.05)
        return make_jwks()

    cache = JWKSCache(loader, ttl_seconds=30)

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _: cache.get(), range(24)))

    assert len(calls) == 1
    assert all(item == make_jwks() for item in results)


def test_concurrent_refreshes_leave_a_valid_document():
    counter_lock = Lock()
    calls = []

    def loader():
        with counter_lock:
            calls.append(1)
            number = len(calls)
        sleep(0.01)
        return make_jwks(f"synthetic-key-{number}")

    cache = JWKSCache(loader, ttl_seconds=30)
    cache.get()

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: cache.refresh(), range(8)))

    assert len(calls) == 9
    assert len(results) == 8
    assert all(isinstance(result.get("keys"), list) for result in results)
    assert cache.is_valid
    assert cache.get()["keys"][0]["kid"].startswith("synthetic-key-")


def test_failed_refresh_does_not_extend_expiry():
    clock = FakeClock()
    state = {"fail": False}
    calls = []

    def loader():
        calls.append(1)
        if state["fail"]:
            raise OSError("synthetic refresh failure")
        return make_jwks()

    cache = JWKSCache(loader, ttl_seconds=5, clock=clock)
    cache.get()
    clock.advance(4)

    state["fail"] = True
    with pytest.raises(JWKSCacheError):
        cache.refresh()

    assert cache.is_valid

    # The failed refresh must not restart the five-second TTL.
    clock.advance(1.1)
    assert not cache.is_valid

    with pytest.raises(JWKSCacheError):
        cache.get()


def test_invalid_refresh_does_not_replace_existing_entry():
    state = {"document": make_jwks("synthetic-original")}
    cache = JWKSCache(lambda: state["document"], ttl_seconds=30)

    cache.get()
    state["document"] = {"keys": []}

    with pytest.raises(JWKSCacheError):
        cache.refresh()

    # The old entry remains available only until its original expiry.
    assert cache.get()["keys"][0]["kid"] == "synthetic-original"


def test_expired_cache_is_not_marked_valid_after_failed_reload():
    clock = FakeClock()
    state = {"fail": False}

    def loader():
        if state["fail"]:
            raise OSError("synthetic reload failure")
        return make_jwks()

    cache = JWKSCache(loader, ttl_seconds=2, clock=clock)
    cache.get()
    clock.advance(3)
    state["fail"] = True

    with pytest.raises(JWKSCacheError):
        cache.get()

    assert not cache.is_valid


def test_invalidation_and_concurrent_gets_reload_once():
    counter_lock = Lock()
    calls = []

    def loader():
        with counter_lock:
            calls.append(1)
        sleep(0.05)
        return make_jwks()

    cache = JWKSCache(loader)
    cache.get()
    cache.invalidate()

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda _: cache.get(), range(20)))

    assert len(calls) == 2
    assert all(item == make_jwks() for item in results)


def test_returned_documents_are_independent_across_threads():
    cache = JWKSCache(lambda: make_jwks())
    cache.get()

    def mutate_copy(_):
        document = cache.get()
        document["keys"][0]["kid"] = "tampered"
        return document

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(mutate_copy, range(16)))

    assert cache.get()["keys"][0]["kid"] == "synthetic-key-1"


def test_clock_boundary_marks_entry_expired():
    clock = FakeClock()
    cache = JWKSCache(lambda: make_jwks(), ttl_seconds=10, clock=clock)

    cache.get()
    clock.advance(10)

    assert not cache.is_valid


def test_failed_loader_does_not_create_valid_cache():
    def loader():
        raise OSError("synthetic initial failure")

    cache = JWKSCache(loader)

    with pytest.raises(JWKSCacheError):
        cache.get()

    assert not cache.is_valid


def test_refresh_with_valid_data_restarts_ttl():
    clock = FakeClock()
    calls = []

    def loader():
        calls.append(1)
        return make_jwks()

    cache = JWKSCache(loader, ttl_seconds=10, clock=clock)
    cache.get()
    clock.advance(8)
    cache.refresh()

    clock.advance(3)
    assert cache.is_valid
    assert len(calls) == 2