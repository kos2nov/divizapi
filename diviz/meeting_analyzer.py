import os
from typing import Any, Dict
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .fireflies import as_plain_text

logger = logging.getLogger(__name__)

class MeetingAnalyzer:
    """Encapsulates logic to analyze meeting transcripts.

    Currently computes:
    - speaker_minutes: aggregated speaking time (in minutes) per speaker
    - total_duration_minutes: total speaking time across all speakers (in minutes)
    """
# service_tier="flex",
    def __init__(self):
        self.openai_client = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
            temperature=0.2,
            max_tokens=100000,
            timeout=120,
           # service_tier="flex",
        )

    def analyze(self, agenda: str, transcript: Dict[str, Any]) -> Dict[str, Any]:
        """Compute stats and generate AI feedback for a transcript.

        Returns a dict with keys: 'stats' and 'feedback'.
        """
        stats = self.calculate_stats(transcript)
        try:
            feedback = self.generate_feedback_openai(agenda, transcript)
        except Exception as e:
            feedback = f"Feedback generation failed: {e}"
        return {
            "stats": stats,
            "feedback": feedback,
        }

    def calculate_stats(self, transcript: Dict[str, Any]) -> Dict[str, Any]:
        speaker_times: Dict[str, float] = {}
        total_duration: float = 0.0

        # Defensive: ensure we have a list of sentences
        sentences = transcript.get("sentences", []) or []
        for sentence in sentences:
            try:
                speaker = sentence.get("speaker_name", "Unknown") or "Unknown"
                start = float(sentence.get("start_time", 0) or 0)
                end = float(sentence.get("end_time", 0) or 0)
                duration = max(0.0, end - start)
            except (TypeError, ValueError):
                # Skip malformed sentence entries
                continue

            speaker_times[speaker] = speaker_times.get(speaker, 0.0) + duration
            total_duration += duration

        return {
            "speaker_minutes": {
                speaker: round(seconds / 60.0, 2)
                for speaker, seconds in speaker_times.items()
            },
            "total_duration_minutes": round(total_duration / 60.0, 2),
        }

    def generate_feedback_openai(self, agenda: str, transcript: Dict[str, Any]) -> str:
        """Generate meeting feedback using an LLM.

        Reads OPENAI_API_KEY from the environment. Converts transcript to readable text
        and asks the model to analyze coverage against agenda and participant contributions.
        """
        template = """
Given the following meeting agenda and transcript, please provide a detailed analysis.

## Agenda
{agenda}

## Meeting Transcript
{transcript}

## Analysis Instructions
Analyze the meeting transcript against the agenda items and present your findings in two parts:

1.  **Agenda Coverage:**
    * List each agenda item.
    * For each item, state whether it was discussed.
    * If discussed, quote the specific lines or dialogue from the script that correspond to that item. If not discussed, state that.
    * Example: "Project Zeus Kick-off: Discussed. Relevant script: 'John: "Good morning, everyone. Let's start with our agenda. First, Project Zeus...'"

2.  **Participant Contributions:**
    * For each participant (e.g., John, Jane, Mike), list the agenda items they contributed to.
    * Briefly describe the nature of their contribution (e.g., initiating the topic, providing an update, raising a concern).
    * Example: "John: Contributed to Project Zeus Kick-off (initiated discussion) and Q3 Budget Review (suggested follow-up)."
"""

        prompt_template = ChatPromptTemplate.from_template(template)
        transcript_text = as_plain_text(transcript)
        agenda_text = agenda.get("title") + "\n" + agenda.get("description")

        prompt = prompt_template.invoke({
            "agenda": agenda_text,
            "transcript": transcript_text,
        })
        result = self.openai_client.invoke(prompt)
        response = result.content
        logger.info("Meeting analysis response: %s", response)
        return response

        
        