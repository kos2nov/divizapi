#!/usr/bin/env python3
"""
Fireflies.ai GraphQL helper and CLI to fetch Google Meet transcripts

Docs used: https://docs.fireflies.ai/llms-full.txt
"""

import os
import re
import json
import asyncio
import click
import datetime as dt
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
import logging

FIREFLIES_ENDPOINT = "https://api.fireflies.ai/graphql"

logger = logging.getLogger(__name__)

# Load environment variables
if not os.getenv("FIREFLIES_API_KEY"):
    load_dotenv()

FIREFLIES_API_KEY = os.getenv("FIREFLIES_API_KEY")


class Fireflies:
    """Fireflies.ai GraphQL client for fetching Google Meet transcripts"""
    
    FIREFLIES_ENDPOINT = "https://api.fireflies.ai/graphql"
    
    TRANSCRIPTS_QUERY = """
query Transcripts($mine: Boolean, $limit: Int, $skip: Int, $fromDate: DateTime, $toDate: DateTime, $keyword: String) {
  transcripts(mine: $mine, limit: $limit, skip: $skip, fromDate: $fromDate, toDate: $toDate, keyword: $keyword) {
    id
    title
    date
    transcript_url
    meeting_link
  }
}
"""
    
    TRANSCRIPT_QUERY = """
query Transcript($id: String!) {
  transcript(id: $id) {
    id
    title
    organizer_email
    meeting_link
    date
    duration
    speakers { id name }
    sentences {
      index
      speaker_name
      text
      raw_text
      start_time
      end_time
    }
    summary {
      overview
      short_summary
      bullet_gist
      action_items
      topics_discussed
    }
  }
}
"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key if api_key else os.getenv("FIREFLIES_API_KEY")
    
    async def _graphql_request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        async with httpx.AsyncClient() as client:
            resp = await client.post(self.FIREFLIES_ENDPOINT, headers=headers, json=payload, timeout=30)
            try:
                data = resp.json()
            except Exception as e:  # pragma: no cover - defensive
                raise ValueError(f"Invalid JSON from Fireflies API: {e}\nStatus: {resp.status_code}\nBody: {resp.text[:300]}")
            
            if resp.status_code != 200 or "errors" in data:
                errs = data.get("errors") or [{"message": resp.text, "code": str(resp.status_code)}]
                first = errs[0]
                code = first.get("code") or first.get("extensions", {}).get("code") or "unknown_error"
                msg = first.get("message") or json.dumps(first)
                raise ValueError(f"Fireflies API error [{code}]: {msg}")
        
        return data.get("data", {})
    
    @staticmethod
    def _iso(dt_obj: dt.datetime) -> str:
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=dt.timezone.utc)
        return dt_obj.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    
    async def list_recent_transcripts(self, days: int = 30, mine: bool = True, limit: int = 50) -> List[Dict[str, Any]]:
        now = dt.datetime.now(dt.timezone.utc)
        from_dt = now - dt.timedelta(days=days)
        variables = {
            "mine": mine,
            "limit": min(max(limit, 1), 50),
            "skip": 0,
            "fromDate": self._iso(from_dt),
            "toDate": self._iso(now),
        }
        async with httpx.AsyncClient() as client:
            data = await self._graphql_request(self.TRANSCRIPTS_QUERY, variables)

        return data.get("transcripts", [])
    
    async def find_transcript_by_meet_code(self, meet_code: str, days: int = 30) -> Optional[Dict[str, Any]]:
        candidates = await self.list_recent_transcripts(days=days, mine=True, limit=50)
        
        def norm(s: Optional[str]) -> str:
            return (s or "").strip().lower()
        
        for t in candidates:
            link = norm(t.get("meeting_link"))
            if not link:
                continue
            if meet_code in link:
                return t
        return None
    
    async def get_transcript_detail(self, transcript_id: str) -> Dict[str, Any]:
        variables = {"id": transcript_id}
        data = await self._graphql_request(self.TRANSCRIPT_QUERY, variables)
        tr = data.get("transcript")
        return tr
    
    def _merge_consecutive_sentences(self, sentences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge consecutive sentences with the same speaker.
        
        - Concatenate text fragments with a single space.
        - Start time is the first segment's start_time.
        - End time is the last segment's end_time.
        - Index is reassigned sequentially.
        """
        if not sentences:
            return []

        merged: List[Dict[str, Any]] = []
        current: Optional[Dict[str, Any]] = None

        for s in sentences or []:
            speaker = s.get("speaker_name")
            text_part = (s.get("text") or s.get("raw_text") or "").strip()
            raw_part = (s.get("raw_text") or s.get("text") or "").strip()

            if current and current.get("speaker_name") == speaker:
                if text_part:
                    current.setdefault("_text_parts", []).append(text_part)
                if raw_part:
                    current.setdefault("_raw_parts", []).append(raw_part)
                # Update end_time to the latest of the group
                current["end_time"] = s.get("end_time", current.get("end_time"))
            else:
                # finalize previous
                if current:
                    merged.append(current)
                # start new
                current = {
                    "speaker_name": speaker,
                    "_text_parts": [text_part] if text_part else [],
                    "_raw_parts": [raw_part] if raw_part else [],
                    "start_time": s.get("start_time"),
                    "end_time": s.get("end_time"),
                }

        if current:
            merged.append(current)

        # finalize shape and re-index
        finalized: List[Dict[str, Any]] = []
        for idx, m in enumerate(merged):
            finalized.append({
                "index": idx,
                "speaker_name": m.get("speaker_name"),
                "text": " ".join(m.get("_text_parts", [])).strip(),
                "raw_text": " ".join(m.get("_raw_parts", [])).strip(),
                "start_time": m.get("start_time"),
                "end_time": m.get("end_time"),
            })

        return finalized
    
    async def get_transcript_by_meet_code(self, meet_code: str, days: int = 30) -> Dict[str, Any]:
        """
        Get a transcript by Google Meet code with full details in API response format.
        
        Args:
            meet_code: The Google Meet code or URL to search for
            days: Number of days to search back (default: 30)
        
        Returns:
            Dict containing transcript details in API response format
        
        Raises:
            ValueError: If transcript is not found
            Exception: For other errors during API calls
        """
        transcript_info = await self.find_transcript_by_meet_code(meet_code, days)
        
        if not transcript_info:
            raise ValueError(f"No transcript found for meet code '{meet_code}' in the last {days} days")
        
        transcript = await self.get_transcript_detail(transcript_info["id"])

        if not transcript:
            return {
                "transcript_id": transcript_info["id"],
                "title": transcript_info.get("title", ""),
                "meeting_link": transcript_info.get("meeting_link", ""),
                "date": transcript_info.get("date", ""),
                "summary": "Error: transcript details not found",
            }

        merged_sentences = self._merge_consecutive_sentences(transcript.get("sentences", []))

        return {
            "transcript_id": transcript["id"],
            "title": transcript.get("title", ""),
            "meeting_link": transcript.get("meeting_link", ""),
            "date": transcript.get("date", ""),
            "duration": transcript.get("duration", ""),
            "speakers": transcript.get("speakers", []),
            "sentences": merged_sentences,
            "summary": transcript.get("summary", {}),
            "organizer_email": transcript.get("organizer_email", "")
        }


def as_plain_text(transcript: Dict[str, Any]) -> str:
    parts: List[str] = []
    title = transcript.get("title")
    if title:
        parts.append(f"# {title}")
    for s in transcript.get("sentences", []) or []:
        speaker = s.get("speaker_name") or ""
        text = s.get("text") or s.get("raw_text") or ""
        if speaker:
            parts.append(f"{speaker}: {text}")
        else:
            parts.append(text)
    return "\n".join(parts)


@click.group()
def cli():
    """Fireflies.ai Google Meet Transcript CLI.

    Set FIREFLIES_API_KEY in your environment or pass --api-key.
    """
    pass



@cli.command("by-code")
@click.argument("meet_code")
@click.option("--days", default=7, show_default=True, help="How many days back to search")
@click.option("--format", "fmt", type=click.Choice(["json", "text"], case_sensitive=False), default="json")
@click.option("--show-id", is_flag=True, help="When --format=text, also print transcript id on stderr")
def get_by_code(meet_code: str, days: int, fmt: str, show_id: bool) -> None:
    """Find a transcript by Google Meet link or code and print it."""
    click.echo(f"Searching recent transcripts (last {days} days) for meet: {meet_code}", err=True)
    fireflies = Fireflies(api_key=FIREFLIES_API_KEY)
    try:
        transcript = asyncio.run(fireflies.get_transcript_by_meet_code(meet_code, days))
    except ValueError as e:
        click.echo(str(e), err=True)
        return
    
    if fmt.lower() == "json":
        click.echo(json.dumps(transcript, indent=2))
    else:
        if show_id:
            click.echo(f"Transcript ID: {transcript['transcript_id']}", err=True)
        click.echo(as_plain_text(transcript))


@cli.command("by-id")
@click.argument("transcript_id")
@click.option("--format", "fmt", type=click.Choice(["json", "text"], case_sensitive=False), default="json")
@click.option("--show-id", is_flag=True)
def get_by_id(transcript_id: str, fmt: str, show_id: bool) -> None:
    """Fetch and print a transcript by its Fireflies transcript id."""
    fireflies = Fireflies(api_key=FIREFLIES_API_KEY)
    tr = fireflies.get_transcript_detail(transcript_id)
    if fmt.lower() == "json":
        click.echo(json.dumps(tr, indent=2))
    else:
        if show_id:
            click.echo(f"Transcript ID: {tr['id']}", err=True)
        click.echo(as_plain_text(tr))


if __name__ == "__main__":
    cli()

