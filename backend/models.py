from pydantic import BaseModel, Field
from typing import List, Optional

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
    similarity_score: float = Field(..., description="Similarity score from FAISS")
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
