#!/usr/bin/env python3
"""
Fireflies.ai GraphQL helper and CLI to fetch Google Meet transcripts

Docs used: https://docs.fireflies.ai/llms-full.txt
"""

import os
import re
import json
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
        
        logger.info("Fireflies call headers: %s", headers)

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
    t = fireflies.find_transcript_by_meet_code(meet_code, days=days)
    if not t:
        raise click.ClickException("No transcript found for that Google Meet link/code in the recent window.")

    tr = fireflies.get_transcript_detail(t["id"])

    if fmt.lower() == "json":
        click.echo(json.dumps(tr, indent=2))
    else:
        if show_id:
            click.echo(f"Transcript ID: {tr['id']}", err=True)
        click.echo(as_plain_text(tr))


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

