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
