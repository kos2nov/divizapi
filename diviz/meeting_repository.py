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
    
    def save_analysis(
        self, 
        user_id: str, 
        meeting_code: str, 
        agenda: Dict[str, str], 
        transcript: Dict[str, Any], 
        analysis: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
    ) -> MeetingAnalysis:
        """Save or update a meeting analysis.
        
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
    
    def get_analysis(self, user_id: str, meeting_code: str) -> Optional[MeetingAnalysis]:
        """Retrieve a meeting analysis by user ID and meeting code.
        
        Args:
            user_id: The ID of the user who owns the analysis
            meeting_code: The meeting code/identifier
            
        Returns:
            The MeetingAnalysis if found, None otherwise
        """
        user_meetings = self._store.get(user_id, {})
        return user_meetings.get(meeting_code)
    
    def list_user_analyses(self, user_id: str) -> List[MeetingAnalysis]:
        """List all meeting analyses for a user.
        
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

# Create a singleton instance
meeting_repository = MeetingRepository()
