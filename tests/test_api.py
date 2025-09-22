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
        assert "/api/meet" in data["endpoints"]


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


    def test_user_endpoint_requires_auth_or_config(self):
        """GET /api/user should require auth or return config error depending on environment."""
        response = self.client.get("/api/user")
        assert response.status_code in (401, 501)
        detail = response.json().get("detail")
        assert detail in ("Missing or invalid Authorization header", "Cognito auth not configured")

    def test_review_endpoint_requires_auth_or_config(self):
        """GET /api/meet/{code} should require auth or return config error depending on environment."""
        response = self.client.get("/api/meet/abc-defg-hjk")
        assert response.status_code in (401, 501)
        detail = response.json().get("detail")
        assert detail in ("Missing or invalid Authorization header", "Cognito auth not configured")


class TestMeetingsEndpoints:
    def test_list_meetings_empty(self, auth_client):
        r = auth_client.get("/api/meetings")
        assert r.status_code == 200
        assert r.json() == []

    def test_get_meeting_details_not_found(self, auth_client):
        r = auth_client.get("/api/meetings/not-exist")
        assert r.status_code == 404
        assert r.json()["detail"] == "Meeting not found"

    def test_delete_meeting_not_found(self, auth_client):
        r = auth_client.delete("/api/meetings/not-exist")
        assert r.status_code == 404
        assert r.json()["detail"] == "Meeting not found"

    def test_create_meeting_success_and_crud_flow(self, auth_client, monkeypatch):
        # Mock Fireflies transcript fetch used by create_meeting
        async def _get_transcript_by_meet_code(self, meet_code: str, days: int = 30):
            return {
                "transcript_id": "t1",
                "title": "My Meeting",
                "meeting_link": f"https://meet.google.com/{meet_code}",
                "date": "2025-01-01T00:00:00Z",
                "duration": 3600,
                "speakers": [],
                "sentences": [
                    {"index": 0, "speaker_name": "Alice", "text": "Hello", "raw_text": "Hello", "start_time": 0, "end_time": 5}
                ],
                "summary": {},
                "organizer_email": "alice@example.com",
            }
        from diviz.fireflies import Fireflies
        monkeypatch.setattr(Fireflies, "get_transcript_by_meet_code", _get_transcript_by_meet_code, raising=True)

        payload = {
            "meet_code": "abc-defg-hjk",
            "title": "My Meeting",
            "description": "desc",
            "start_time": "2025-01-01T00:00:00Z",
            "end_time": "2025-01-01T01:00:00Z",
        }
        # Create
        r = auth_client.post("/api/meetings", json=payload)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "success"

        # List
        r = auth_client.get("/api/meetings")
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list) and len(items) == 1
        assert items[0]["meeting_code"] == "abc-defg-hjk"

        # Get details
        r = auth_client.get("/api/meetings/abc-defg-hjk")
        assert r.status_code == 200
        details = r.json()
        assert details["agenda"]["title"] == "My Meeting"
        assert details["transcript"]["transcript_id"] == "t1"

        # Delete
        r = auth_client.delete("/api/meetings/abc-defg-hjk")
        assert r.status_code == 204

        # Ensure gone
        r = auth_client.get("/api/meetings/abc-defg-hjk")
        assert r.status_code == 404

    def test_create_meeting_failure_when_fireflies_errors(self, auth_client, monkeypatch):
        async def _get_transcript_by_meet_code(self, meet_code: str, days: int = 30):
            raise Exception("service down")
        from diviz.fireflies import Fireflies
        monkeypatch.setattr(Fireflies, "get_transcript_by_meet_code", _get_transcript_by_meet_code, raising=True)

        payload = {
            "meet_code": "abc-defg-hjk",
            "title": "My Meeting",
            "description": "desc",
            "start_time": "2025-01-01T00:00:00Z",
            "end_time": "2025-01-01T01:00:00Z",
        }
        r = auth_client.post("/api/meetings", json=payload)
        assert r.status_code == 500
        assert "Failed to retrieve transcript" in r.json().get("detail", "")
