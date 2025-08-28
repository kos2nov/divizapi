"""
Integration tests for the FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from diviz.main import app


class TestAPI:
    """Test cases for the API endpoints."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Test the root endpoint returns service information."""
        response = self.client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "DiViz API Service"
        assert data["version"] == "0.0.1"
        assert "endpoints" in data
        assert "/review" in data["endpoints"]


    def test_api_documentation_endpoints(self):
        """Test that API documentation endpoints are accessible."""
        # Test OpenAPI schema
        response = self.client.get("/openapi.json")
        assert response.status_code == 200

        # Test Swagger UI
        response = self.client.get("/docs")
        assert response.status_code == 200

        # Test ReDoc
        response = self.client.get("/redoc")
        assert response.status_code == 200
