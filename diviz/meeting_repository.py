from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
from pydantic import BaseModel


class MeetingAnalysis(BaseModel):
    """Represents the analysis of a meeting."""
    user_id: str
    meeting_code: str
    start_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    agenda: Dict[str, str]
    transcript: Dict[str, Any]
    analysis: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class MeetingRepository:
    """In-memory repository for storing and retrieving meeting analyses."""
    
    def __init__(self):
        self._store: Dict[str, Dict[str, MeetingAnalysis]] = {}
    
    def save(
        self, 
        user_id: str, 
        meeting_code: str, 
        agenda: Dict[str, str], 
        transcript: Dict[str, Any], 
        analysis: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
    ) -> MeetingAnalysis:
        """Save or update a meeting record.
        
        Args:
            user_id: The ID of the user who owns this analysis
            meeting_code: The meeting code/identifier
            agenda: Meeting agenda with title and description
            transcript: Raw transcript data
            analysis: Analysis results from MeetingAnalyzer
            
        Returns:
            The saved MeetingAnalysis object
        """
        now = datetime.now(timezone.utc)
        meeting_analysis = MeetingAnalysis(
            user_id=user_id,
            meeting_code=meeting_code,
            start_time=start_time,
            duration_minutes=duration_minutes,
            agenda=agenda,
            transcript=transcript,
            analysis=analysis,
            created_at=now,
            updated_at=now
        )
        
        if user_id not in self._store:
            self._store[user_id] = {}
            
        self._store[user_id][meeting_code] = meeting_analysis
        return meeting_analysis
    
    def update(self, user_id: str, meeting: MeetingAnalysis) -> MeetingAnalysis:
        """Update an existing meeting record."""
        if user_id not in self._store:
            raise ValueError(f"User {user_id} not found")
        if meeting.meeting_code not in self._store[user_id]:
            raise ValueError(f"Meeting {meeting.meeting_code} not found for user {user_id}")
        self._store[user_id][meeting.meeting_code] = meeting
        return meeting

    def get(self, user_id: str, meeting_code: str) -> Optional[MeetingAnalysis]:
        """Retrieve a meeting by user ID and meeting code.
        
        Args:
            user_id: The ID of the user who owns the analysis
            meeting_code: The meeting code/identifier
            
        Returns:
            The MeetingAnalysis if found, None otherwise
        """
        user_meetings = self._store.get(user_id, {})
        return user_meetings.get(meeting_code)
    
    def list_user_meetings(self, user_id: str) -> List[MeetingAnalysis]:
        """List all stored meetings for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of MeetingAnalysis objects, most recent first
        """
        user_meetings = self._store.get(user_id, {})
        return sorted(
            list(user_meetings.values()),
            key=lambda x: x.updated_at,
            reverse=True
        )
    
    def delete(self, user_id: str, meeting_code: str) -> bool:
        """Delete a stored meeting for a user by meeting code.
        
        Args:
            user_id: The ID of the user who owns the analysis
            meeting_code: The meeting code/identifier to delete
        
        Returns:
            True if the record was deleted, False if it did not exist
        """
        user_meetings = self._store.get(user_id)
        if not user_meetings:
            return False
        if meeting_code in user_meetings:
            del user_meetings[meeting_code]
            # Clean up empty user bucket to keep store tidy
            if not user_meetings:
                del self._store[user_id]
            return True
        return False

# Create a singleton instance
meeting_repository = MeetingRepository()
