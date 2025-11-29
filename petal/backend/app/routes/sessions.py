"""Session management endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from supabase import Client
from typing import List
import asyncio

from app.models import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionDetailResponse,
    SessionPreviewResponse,
    DeleteResponse
)
from app.database import get_db
from app.services.sessions import SessionService
from app.services.cache import session_cache
from app.services.claude import claude_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_session_service(db: Client = Depends(get_db)) -> SessionService:
    """Dependency to get SessionService instance."""
    return SessionService(db)


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    session: SessionCreate,
    service: SessionService = Depends(get_session_service)
):
    """
    Create a new session.

    Args:
        session: Session creation data

    Returns:
        Created session data
    """
    try:
        result = await service.create_session(
            user_id=session.user_id,
            name=session.name,
            icon=session.icon,
            description=session.description
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to create session")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=List[SessionResponse])
async def get_user_sessions(
    user_id: str,
    service: SessionService = Depends(get_session_service)
):
    """
    Get all sessions for a user.

    Args:
        user_id: User ID

    Returns:
        List of user's sessions
    """
    try:
        sessions = await service.get_user_sessions(user_id)
        return sessions

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detail/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    service: SessionService = Depends(get_session_service)
):
    """
    Get a single session with details.

    Args:
        session_id: Session ID

    Returns:
        Session details including memory count
    """
    try:
        session = await service.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return session

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    update_data: SessionUpdate,
    service: SessionService = Depends(get_session_service)
):
    """
    Update a session.

    Args:
        session_id: Session ID
        update_data: Fields to update

    Returns:
        Updated session data
    """
    try:
        result = await service.update_session(
            session_id=session_id,
            name=update_data.name,
            icon=update_data.icon,
            description=update_data.description
        )

        if not result:
            raise HTTPException(status_code=404, detail="Session not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}", response_model=DeleteResponse)
async def delete_session(
    session_id: str,
    service: SessionService = Depends(get_session_service)
):
    """
    Delete a session.

    Args:
        session_id: Session ID

    Returns:
        Deletion confirmation
    """
    try:
        await service.delete_session(session_id)

        # Invalidate cache for deleted session
        session_cache.invalidate_session(session_id)

        return DeleteResponse(status="deleted", id=session_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/activate")
async def activate_session(
    session_id: str,
    service: SessionService = Depends(get_session_service)
):
    """
    Activate a session and warm its cache.

    Call this when user switches to a session to pre-load data into Redis
    for faster subsequent operations.

    Args:
        session_id: Session ID to activate

    Returns:
        Activation status
    """
    try:
        # Get session data
        session = await service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get recent memories (limit to 50 for cache warming)
        memories_result = await service.get_session_memories(session_id, limit=50)

        # Warm cache in background (non-blocking)
        asyncio.create_task(
            session_cache.warm_session_cache(
                session_id=session_id,
                session_data=session,
                memories=memories_result["memories"]
            )
        )

        return {
            "status": "activated",
            "session_id": session_id,
            "cached_memories": len(memories_result["memories"])
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/preview", response_model=SessionPreviewResponse)
async def get_session_preview(
    session_id: str,
    service: SessionService = Depends(get_session_service)
):
    """
    Get session preview for hover tooltip.

    Returns session name, memory count, description, and recent memories.
    Description is generated by Claude if not exists, and cached permanently.

    Args:
        session_id: Session ID

    Returns:
        Session preview data
    """
    try:
        import logging
        logger = logging.getLogger(__name__)

        # Get session
        session = await service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get recent memories (last 3 for preview)
        memories_result = await service.get_session_memories(session_id, limit=3)
        memories = memories_result["memories"]

        # Truncate memory texts to 100 chars
        recent_memories = [
            mem["processed_text"][:100] + ("..." if len(mem["processed_text"]) > 100 else "")
            for mem in memories
        ]

        # Get or generate description
        description = session.get("description")

        if not description:
            # Check cache first
            cached_description = session_cache.get_session_description(session_id)

            if cached_description:
                logger.info(f"Using cached description for session {session_id}")
                description = cached_description
            else:
                # Generate description with Claude
                logger.info(f"Generating description for session {session_id}")

                if memories:
                    # Get more memories for better description (up to 20)
                    all_memories_result = await service.get_session_memories(session_id, limit=20)
                    memory_texts = [m["processed_text"] for m in all_memories_result["memories"]]

                    description = await claude_service.generate_session_description(memory_texts)

                    # Cache the generated description
                    session_cache.set_session_description(session_id, description)
                else:
                    description = "No memories yet in this session."

        return SessionPreviewResponse(
            session_name=session["name"],
            memory_count=session.get("memory_count", 0),
            description=description,
            recent_memories=recent_memories
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
