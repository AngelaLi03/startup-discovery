from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SearchResult(BaseModel):
    """Model for search result."""
    id: int
    name: str
    description: str
    industry: str
    funding: str
    location: str
    founded: int
    team_size: int
    similarity_score: float = Field(..., description="Raw similarity score from FAISS (0-1)")
    similarity_percentage: float = Field(..., description="Calibrated similarity score (0-100)")
    similarity_label: str = Field(..., description="Human-readable similarity description")
    similarity_color: str = Field(..., description="Emoji indicator for similarity level")
    match_reason: str = Field(..., description="Explanation of why this startup matched")
    calibration_info: Dict[str, Any] = Field(..., description="Z-score and background distribution info")
    
    # Optional fields that might be present in the data
    source: Optional[str] = None
    source_id: Optional[str] = None
    content_hash: Optional[str] = None
    updated_at: Optional[str] = None
    homepage_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    rank: int = Field(..., description="Rank in search results")

class AskResponse(BaseModel):
    """Model for Q&A response."""
    question: str
    answer: str

class HealthResponse(BaseModel):
    """Model for health check response."""
    status: str
    index_loaded: bool
    startup_count: Optional[int] = None

class ErrorResponse(BaseModel):
    """Model for error responses."""
    detail: str
    error_type: Optional[str] = None
