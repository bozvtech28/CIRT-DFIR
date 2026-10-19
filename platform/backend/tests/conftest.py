"""Shared test fixtures for the backend suite.

Keep authentication overrides local to tests that explicitly need a synthetic
principal. In particular, never install a global/autouse identity that can
mask the application's fail-closed authentication behavior.
"""

import pytest


@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    """Prevent FastAPI dependency overrides leaking between tests."""
    from app.main import app

    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
