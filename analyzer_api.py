#!/usr/bin/env python3
"""
Script to analyze a meeting transcript by calling the /api/analyze/transcript/ endpoint.

Usage:
    export ACCESS_TOKEN=your_access_token_here
    python analyze_transcript.py agenda.json transcript.json [--api-url URL]
"""

import argparse
import json
import os
import sys
from typing import Dict, Any

import httpx


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file {file_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


async def analyze_transcript(api_url: str, access_token: str, agenda: Dict[str, str], transcript: Dict[str, Any]) -> Dict[str, Any]:
    """Call the analyze transcript API endpoint asynchronously."""
    url = f"{api_url.rstrip('/')}/api/analyze/transcript/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "agenda": agenda,
        "transcript": transcript
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Response status: {e.response.status_code}", file=sys.stderr)
            try:
                print(f"Response body: {e.response.text}", file=sys.stderr)
            except Exception:
                pass
        sys.exit(1)
    except Exception as e:
        print(f"Error calling API: {e}", file=sys.stderr)
        sys.exit(1)


async def main():
    parser = argparse.ArgumentParser(description='Analyze a meeting transcript')
    parser.add_argument('agenda_file', help='Path to the agenda JSON file')
    parser.add_argument('transcript_file', help='Path to the transcript JSON file')
    parser.add_argument('--api-url', default='http://localhost:8000',
                       help='Base URL of the API (default: http://localhost:8000)')
    
    args = parser.parse_args()
    
    # Get access token from environment
    access_token = os.environ.get('ACCESS_TOKEN')
    if not access_token:
        print("Error: ACCESS_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    # Load input files
    agenda = load_json_file(args.agenda_file)
    transcript = load_json_file(args.transcript_file)
    
    # Call the API asynchronously
    result = await analyze_transcript(args.api_url, access_token, agenda, transcript)
    
    # Print pretty-printed JSON output
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
