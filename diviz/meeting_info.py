#!/usr/bin/env python3
import os
import click
import json
import pickle
from typing import Dict, Any, Optional
from datetime import datetime, UTC
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/meetings.space.created',
    'https://www.googleapis.com/auth/calendar.readonly'
]

class MeetingAPI:
    def __init__(self, credentials_file: str = 'credentials.json'):
        """
        Initialize the Google Meet API client.
        
        Args:
            credentials_file: Path to the OAuth 2.0 credentials JSON file.
        """
        self.credentials_file = credentials_file
        self.creds = None
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate using OAuth 2.0 credentials."""
        # The file token.pickle stores the user's access and refresh tokens.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
        
        self.service = build('calendar', 'v3', credentials=self.creds)
    
    def get_meeting_details(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch meeting details from Google Calendar/Meet API.
        
        Args:
            meeting_id: The Google Meet conference ID or event ID.
            
        Returns:
            Dict containing meeting details or None if not found.
        """
        try:
            # First try to get the event by ID
            try:
                event = self.service.events().get(
                    calendarId='primary',
                    eventId=meeting_id,
                ).execute()
            except HttpError as e:
                if 'Not Found' in str(e):
                    # If event not found by ID, try to search by conference ID
                    now = datetime.now(UTC).isoformat() + 'Z'  # 'Z' indicates UTC time
                    events_result = self.service.events().list(
                        calendarId='primary',
                        q=meeting_id,
                        timeMin=now,
                        maxResults=1,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    events = events_result.get('items', [])
                    
                    if not events:
                        return None
                    event = events[0]
                else:
                    raise
            
            # Extract meeting details using the helper method
            return self._extract_meeting_details(event)
            
        except HttpError as error:
            click.echo(f"An error occurred: {error}", err=True)
            return None

    def get_conference(self, conf_id: str, date: Optional[datetime] = None):
        """
        Fetch meeting details by video conference ID from Google Calendar/Meet API.

        Args:
            conf_id: The Google Meet conference ID or event ID.
            date: Optional date to search around (defaults to current time).

        Returns:
            Dict containing meeting details or None if not found.
        """
        meeting_details = self.find_meeting(conf_id, date)
        return meeting_details


    def find_meeting(self, conf_id: str, date: datetime = datetime.now(UTC)) -> Optional[Dict[str, Any]]:
        """
        Find meeting details by video conference ID.

        Args:
            conf_id: The Google Meet conference ID (e.g., 'abc-defg-hij').
            date: Optional date to search around (defaults to current time).

        Returns:
            Dict containing meeting details or None if not found.
        """
        try:

            # Use provided date or default to current time
            if date is None:
                search_date = datetime.now(UTC)
            else:
                search_date = date

            # Search for events around the specified date (±1 day)
            time_min = search_date.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
            time_max = search_date.replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%SZ")

            # Search for events that might contain the conference ID
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=100,  # Get more events to search through
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            # Search through events for matching conference ID
            for event in events:
                conference_data = event.get('conferenceData', {})
                entry_points = conference_data.get('entryPoints', [])

                # Check if any entry point contains the conference ID
                for entry_point in entry_points:
                    if entry_point.get('entryPointType') == 'video':
                        # Check meeting code
                        meeting_code = entry_point.get('meetingCode', '')
                        if meeting_code == conf_id:
                            return self._extract_meeting_details(event)

                        # Check if conference ID is in the URI
                        uri = entry_point.get('uri', '')
                        if conf_id in uri:
                            return self._extract_meeting_details(event)

                # Also check if conference ID is mentioned in the event description or summary
                description = event.get('description', '').lower()
                summary = event.get('summary', '').lower()
                if conf_id.lower() in description or conf_id.lower() in summary:
                    return self._extract_meeting_details(event)

            return None

        except HttpError as error:
            click.echo(f"An error occurred while searching for meeting: {error}", err=True)
            return None

    def _extract_meeting_details(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract meeting details from a Google Calendar event.

        Args:
            event: Google Calendar event object.

        Returns:
            Dict containing formatted meeting details.
        """
        conference_data = event.get('conferenceData', {})
        entry_points = conference_data.get('entryPoints', [])
        video_entry = next((ep for ep in entry_points if ep.get('entryPointType') == 'video'), {})

        attendees = [
            attendee.get('email', attendee.get('displayName', 'Unknown'))
            for attendee in event.get('attendees', [])
            if attendee.get('self', False) is False  # Exclude the organizer
        ]

        return {
            'event_id': event.get('id', ''),
            'title': event.get('summary', 'No title'),
            'description': event.get('description', ''),
            'start_time': event.get('start', {}).get('dateTime'),
            'end_time': event.get('end', {}).get('dateTime'),
            'meet_link': video_entry.get('uri', ''),
            'meeting_code': video_entry.get('meetingCode', ''),
            'attendees': attendees,
            'organizer': event.get('organizer', {}).get('email', 'Unknown')
        }

@click.group()
def cli():
    """Google Meet Information CLI tool."""
    pass

@cli.command()
@click.argument('meeting_id')
@click.option('--credentials', '-c', default='credentials.json',
              help='Path to Google OAuth 2.0 credentials JSON file')
def get_meeting_info(meeting_id: str, credentials: str):
    """
    CLI tool to fetch and display Google Meet information by meeting ID or event ID.
    
    The meeting ID can be either:
    - Google Calendar event ID
    - Google Meet conference ID (from the meeting URL)
    
    Example:
        python meeting_info.py abc123xyz
        python meeting_info.py abc123xyz --output json
        python meeting_info.py abc123xyz --credentials /path/to/credentials.json
    """
    try:
        api = meeting_api(credentials)

        click.echo(f"Fetching details for meeting: {meeting_id}", err=True)
        meeting_data = api.get_meeting_details(meeting_id)
        
        if not meeting_data:
            raise click.ClickException(f"No meeting found with ID: {meeting_id}")
        
        # Format the output
        out = {
            "meeting_id": meeting_id,
            "title": meeting_data["title"],
            "description": meeting_data["description"],
            "start_time": meeting_data["start_time"],
            "end_time": meeting_data["end_time"],
            "meet_link": meeting_data["meet_link"],
            "meeting_code": meeting_data["meeting_code"],
            "organizer": meeting_data["organizer"],
            "attendees": meeting_data["attendees"]
        }

        click.echo(json.dumps(out, indent=2))
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        return 1
    
    return 0

@cli.command()
@click.argument('conf_id')
@click.option('--date', '-d', default=None,
              help='Date to search for meeting (YYYY-MM-DD format, defaults to today)')
@click.option('--credentials', '-c', default='credentials.json',
              help='Path to Google OAuth 2.0 credentials JSON file')
def conf_info(conf_id: str, date: str, credentials: str):
    """
    CLI tool to fetch and display Google Meet information by conference ID.

    Args:
        conf_id: The Google Meet conference ID (e.g., 'abc-defg-hij')
        date: Optional date to search around (YYYY-MM-DD format)
        credentials: Path to Google OAuth 2.0 credentials JSON file

    Example:
        python meeting_info.py conf-info abc-defg-hij
        python meeting_info.py conf-info abc-defg-hij --date 2025-08-12
    """
    try:
        api = meeting_api(credentials)

        # Parse date if provided
        search_date = None
        if date:
            try:
                search_date = datetime.fromisoformat(date).replace(tzinfo=UTC)
            except ValueError:
                raise click.ClickException(f"Invalid date format: {date}. Use YYYY-MM-DD format.")

        click.echo(f"Searching for meeting with conference ID: {conf_id}", err=True)
        meeting_data = api.get_conference(conf_id, search_date)

        if not meeting_data:
            raise click.ClickException(f"No meeting found with conference ID: {conf_id}")

        click.echo(json.dumps(meeting_data, indent=2))

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        return 1

    return 0


def meeting_api(credentials):
    if not os.path.exists(credentials):
        raise click.ClickException(
            f"Credentials file not found: {credentials}\n"
            "Please download your OAuth 2.0 credentials from Google Cloud Console:\n"
            "1. Go to https://console.cloud.google.com/apis/credentials\n"
            "2. Create credentials > OAuth client ID > Desktop app\n"
            f"3. Download the JSON and save as '{credentials}'"
        )
    click.echo("Authenticating with Google...", err=True)
    api = MeetingAPI(credentials_file=credentials)
    return api


if __name__ == "__main__":
    cli()
