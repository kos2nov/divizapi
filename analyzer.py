#!/usr/bin/env python3
"""
Script to analyze a meeting transcript locally using MeetingAnalyzer.

Usage:
    python analyzer.py agenda.json transcript.json
"""

import argparse
import json
import os
import sys
from typing import Dict, Any
from dotenv import load_dotenv

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after setting up path
from diviz.meeting_analyzer import MeetingAnalyzer


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


def analyze_transcript(agenda: Dict[str, str], transcript: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze transcript using MeetingAnalyzer."""
    try:
        analyzer = MeetingAnalyzer()
        return analyzer.analyze(agenda, transcript)
    except Exception as e:
        print(f"Error analyzing transcript: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description='Analyze a meeting transcript locally')
    parser.add_argument('agenda_file', help='Path to the agenda JSON file')
    parser.add_argument('transcript_file', help='Path to the transcript JSON file')
    
    args = parser.parse_args()
    
    # Load input files
    agenda = load_json_file(args.agenda_file)
    transcript = load_json_file(args.transcript_file)
    
    # Analyze the transcript
    result = analyze_transcript(agenda, transcript)
    
    # Print pretty-printed JSON output
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
