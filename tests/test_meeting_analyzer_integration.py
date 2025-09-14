import os
import pytest
from dotenv import load_dotenv

from diviz.meeting_analyzer import MeetingAnalyzer


@pytest.mark.integration
def test_generate_feedback_openai_integration():
    """Integration test that calls OpenAI via LangChain if OPENAI_API_KEY is set.

    The test loads environment variables from .env and skips if no valid key is present.
    """
    # Load variables from .env
    load_dotenv(override=False)
     

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not configured; skipping OpenAI integration test")

    analyzer = MeetingAnalyzer()

    agenda = {"title": "Weekly Standup", "description": "Agenda: - Introductions - Project Apollo status update - Next steps and assignments"}
    

    # Minimal transcript resembling Fireflies format used by the app
    transcript = {
        "title": "Weekly Standup",
        "sentences": [
            {
                "index": 0,
                "speaker_name": "Alice",
                "text": "Good morning everyone, let's start with introductions.",
                "raw_text": "Good morning everyone, let's start with introductions.",
                "start_time": 0,
                "end_time": 7,
            },
            {
                "index": 1,
                "speaker_name": "Bob",
                "text": "Project Apollo is on track; we completed the UI revamp.",
                "raw_text": "Project Apollo is on track; we completed the UI revamp.",
                "start_time": 8,
                "end_time": 16,
            },
            {
                "index": 2,
                "speaker_name": "Carol",
                "text": "Next steps: finalize the API endpoints and prepare assignments.",
                "raw_text": "Next steps: finalize the API endpoints and prepare assignments.",
                "start_time": 17,
                "end_time": 25,
            },
        ],
    }

    feedback = analyzer.generate_feedback_openai(agenda, transcript)

    assert isinstance(feedback, str)
    assert feedback.strip() != ""
    print(feedback)
