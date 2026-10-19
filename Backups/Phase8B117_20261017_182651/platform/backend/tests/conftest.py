"""Test-only identity override for legacy API tests.

This fixture is confined to the test suite. It is not used by the application
outside pytest and does not establish real user identity.
"""
import pytest
from fastapi.testclient import TestClient

from app.auth_dependencies import get_current_principal
from app.main import app
from app.security import Principal, ROLE_ANALYST

@pytest.fixture(autouse=True)
def test_identity_override():
    app.dependency_overrides[get_current_principal] = lambda: Principal(
        subject="synthetic-test-analyst",
        roles=frozenset({ROLE_ANALYST}),
    )
    yield
    app.dependency_overrides.clear()
