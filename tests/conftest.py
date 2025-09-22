"""
Pytest configuration and shared fixtures.
"""

import pytest
from fastapi.testclient import TestClient

from diviz.main import app



@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)





@pytest.fixture
def sample_messages():
    """Provide sample messages for testing."""
    return [
        "Hello World",
        "Test message",
        "123",
        "Special chars: !@#$%",
        "Unicode: 🚀 🎉",
        "Long message with multiple words and punctuation!"
    ]


@pytest.fixture
def empty_messages():
    """Provide empty/whitespace messages for testing."""
    return ["", " ", "  ", "\t", "\n", " \t \n "]


# ---------------------------------------------------------------------------
# Authenticated client fixture and helpers for protected endpoints
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_claims():
    """Default fake user claims used to bypass Cognito in tests."""
    return {"sub": "test-user", "email": "test@example.com", "cognito:username": "tester"}


@pytest.fixture
def auth_client(auth_claims):
    """Test client with dependency override to simulate an authenticated user.
    Also ensures the in-memory meeting repository is clean before and after tests.
    """
    from diviz.main import get_current_user
    import diviz.main as m

    async def _override_user():
        return auth_claims

    # Override auth dependency and clear repo state
    app.dependency_overrides[get_current_user] = _override_user
    m.meeting_repository._store.clear()

    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()
        m.meeting_repository._store.clear()


# ---------------------------------------------------------------------------
# Test selection: skip integration tests by default unless --run-integration
# ---------------------------------------------------------------------------

def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run tests marked as integration",
    )


def pytest_collection_modifyitems(config, items):
    # If user explicitly enabled integration via flag or there is just one test, allow them
    if config.getoption("--run-integration") or len(items) == 1:
        return

    # If user filtered by marker and included 'integration' in expression, allow them
    marker_expr = config.getoption("-m") or ""
    if "integration" in marker_expr:
        return

    # Otherwise, skip integration tests by default
    skip_integration = pytest.mark.skip(reason="integration tests are skipped by default; use --run-integration or -m integration")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
