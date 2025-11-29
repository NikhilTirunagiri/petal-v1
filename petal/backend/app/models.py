"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# Session Models
# ============================================================================

class SessionCreate(BaseModel):
    """Request model for creating a new session."""
    user_id: str
    name: str
    icon: str = "📁"
    description: Optional[str] = None


class SessionUpdate(BaseModel):
    """Request model for updating a session."""
    name: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None


class SessionResponse(BaseModel):
    """Response model for session data."""
    id: str
    user_id: str
    name: str
    icon: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class SessionDetailResponse(SessionResponse):
    """Detailed session response with memory count."""
    memory_count: int = 0


class SessionPreviewResponse(BaseModel):
    """Response model for session preview (hover tooltip)."""
    session_name: str
    memory_count: int
    description: str
    recent_memories: List[str] = Field(default_factory=list, max_length=3)


# ============================================================================
# Memory Models
# ============================================================================

class SmartCopyRequest(BaseModel):
    """Request model for smart copy operation."""
    text: str = Field(..., max_length=50000)
    session_id: str
    user_id: str
    source: Optional[str] = None


class SmartCopyResponse(BaseModel):
    """Response model for smart copy operation."""
    status: str = "saved"
    memory_id: str
    original_length: int
    processed_length: int
    processed_text: str


class SmartPasteResponse(BaseModel):
    """Response model for smart paste operation."""
    formatted_text: str
    memory_count: int
    session_name: str


class MemoryResponse(BaseModel):
    """Response model for individual memory."""
    id: str
    processed_text: str
    created_at: datetime


class MemoriesListResponse(BaseModel):
    """Response model for list of memories."""
    memories: List[MemoryResponse]
    total: int


# ============================================================================
# Personal Memory (Mem0) Models
# ============================================================================

class PersonalMemoryRequest(BaseModel):
    """Request model for adding personal memory."""
    text: str
    user_id: str


class PersonalMemoryResponse(BaseModel):
    """Response model for personal memory operation."""
    status: str = "added"
    message: str = "Added to personal memory"


class PersonalMemory(BaseModel):
    """Model for individual personal memory."""
    id: str
    text: str
    category: Optional[str] = None


class PersonalMemoriesResponse(BaseModel):
    """Response model for list of personal memories."""
    memories: List[PersonalMemory]


# ============================================================================
# Search Models
# ============================================================================

class SearchResult(BaseModel):
    """Model for individual search result."""
    id: str
    processed_text: str
    relevance_score: float


class SearchResponse(BaseModel):
    """Response model for search operation."""
    results: List[SearchResult]
    total: int


# ============================================================================
# Generic Response Models
# ============================================================================

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = "healthy"
    version: str = "1.0.0"


class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    status: str = "deleted"
    id: str = Field(..., description="ID of deleted resource")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    detail: Optional[str] = None
    status_code: int


# ============================================================================
# Chat Models
# ============================================================================

class ChatMessage(BaseModel):
    """Request model for chat messages."""
    message: str = Field(..., min_length=1)
    session_id: str
    user_id: str
    search_scope: str = Field(default="current", pattern="^(current|all)$")


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    intent: str
    response: str
    action_taken: Optional[str] = None
    memories_found: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None
