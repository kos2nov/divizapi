from typing import Any, Dict


class MeetingAnalyzer:
    """Encapsulates logic to analyze meeting transcripts.

    Currently computes:
    - speaker_minutes: aggregated speaking time (in minutes) per speaker
    - total_duration_minutes: total speaking time across all speakers (in minutes)
    """

    def analyze(self, transcript: Dict[str, Any]) -> Dict[str, Any]:
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
