"""Memory management endpoints (smart copy/paste, personal memories, search)."""

from fastapi import APIRouter, HTTPException, Depends, Query
from supabase import Client
from typing import List

from app.models import (
    SmartCopyRequest,
    SmartCopyResponse,
    SmartPasteResponse,
    MemoriesListResponse,
    DeleteResponse,
    PersonalMemoryRequest,
    PersonalMemoryResponse,
    PersonalMemoriesResponse,
    PersonalMemory,
    SearchResponse,
    SearchResult
)
from app.database import get_db
from app.services.sessions import SessionService
from app.services.claude import claude_service
from app.services.mem0_service import mem0_service
from app.services import embeddings
from app.services.cache import session_cache
from app.services.task_queue import task_queue

router = APIRouter(tags=["memories"])


def get_session_service(db: Client = Depends(get_db)) -> SessionService:
    """Dependency to get SessionService instance."""
    return SessionService(db)


def get_embedding_service():
    """Dependency to get EmbeddingService instance."""
    if embeddings.embedding_service is None:
        raise HTTPException(status_code=500, detail="Embedding service not initialized")
    return embeddings.embedding_service


# ============================================================================
# Background Processing Functions
# ============================================================================

async def process_smart_copy_background(
    text: str,
    session_id: str,
    user_id: str,
    source: str,
    embedding_svc,
    service: SessionService
):
    """Background task to process Smart Copy asynchronously."""
    import logging
    import asyncio

    logger = logging.getLogger(__name__)
    logger.info(f"Background processing Smart Copy for session {session_id}")

    try:
        # Run Claude processing and embedding generation IN PARALLEL
        processed_text_task = claude_service.process_text(text)
        embedding_task = embedding_svc.create_embedding(text)

        # Wait for both to complete
        results = await asyncio.gather(
            processed_text_task,
            embedding_task,
            return_exceptions=True
        )

        processed_text = results[0]
        embedding = results[1] if not isinstance(results[1], Exception) else None

        # Log if embedding failed
        if isinstance(results[1], Exception):
            logger.warning(f"Failed to generate embedding: {results[1]}")

        # Save to session_memories with embedding
        memory = await service.save_memory(
            session_id=session_id,
            user_id=user_id,
            original_text=text,
            processed_text=processed_text,
            source=source,
            embedding=embedding
        )

        # Invalidate session memories cache
        session_cache.invalidate_session_memories(session_id)

        # Invalidate description cache (memories changed, description should regenerate)
        session_cache.invalidate_session_description(session_id)

        logger.info(f"Background Smart Copy completed: {memory['id']}")

    except Exception as e:
        logger.error(f"Background Smart Copy failed: {e}", exc_info=True)


# ============================================================================
# Smart Copy & Paste (Main Features)
# ============================================================================

@router.post("/smart-copy", response_model=SmartCopyResponse)
async def smart_copy(
    request: SmartCopyRequest,
    service: SessionService = Depends(get_session_service),
    embedding_svc = Depends(get_embedding_service)
):
    """
    Smart Copy: Process text with Claude and save to session.

    This is the main feature for capturing and processing context.

    Args:
        request: Text to process along with session and user info

    Returns:
        Processed text and metadata
    """
    try:
        import asyncio
        import logging

        # Run Claude processing and embedding generation IN PARALLEL
        # This reduces total time from 3-7s to 2-5s (fastest of the two)
        processed_text_task = claude_service.process_text(request.text)
        embedding_task = embedding_svc.create_embedding(request.text)

        # Wait for both to complete
        results = await asyncio.gather(
            processed_text_task,
            embedding_task,
            return_exceptions=True  # Don't fail if embedding fails
        )

        processed_text = results[0]
        embedding = results[1] if not isinstance(results[1], Exception) else None

        # Log if embedding failed
        if isinstance(results[1], Exception):
            logging.warning(f"Failed to generate embedding: {results[1]}")

        # Save to session_memories with embedding
        memory = await service.save_memory(
            session_id=request.session_id,
            user_id=request.user_id,
            original_text=request.text,
            processed_text=processed_text,
            source=request.source,
            embedding=embedding
        )

        if not memory:
            raise HTTPException(status_code=500, detail="Failed to save memory")

        # Invalidate session memories cache (so next read gets fresh data)
        session_cache.invalidate_session_memories(request.session_id)

        # Invalidate description cache (memories changed, description should regenerate)
        session_cache.invalidate_session_description(request.session_id)

        return SmartCopyResponse(
            status="saved",
            memory_id=memory["id"],
            original_length=len(request.text),
            processed_length=len(processed_text),
            processed_text=processed_text
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Smart copy failed: {str(e)}")


@router.post("/smart-copy/async")
async def smart_copy_async(
    request: SmartCopyRequest,
    service: SessionService = Depends(get_session_service),
    embedding_svc = Depends(get_embedding_service)
):
    """
    Smart Copy (Async): Process text in background, return immediately.

    This endpoint returns immediately with a task ID, and processes the
    text asynchronously in the background. User gets instant feedback.

    Args:
        request: Text to process along with session and user info

    Returns:
        Task ID for tracking (processing happens in background)
    """
    try:
        # Enqueue background task
        task_id = await task_queue.enqueue(
            process_smart_copy_background,
            request.text,
            request.session_id,
            request.user_id,
            request.source or "mac-app",
            embedding_svc,
            service
        )

        return {
            "status": "processing",
            "task_id": task_id,
            "message": "Smart copy queued for processing"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue smart copy: {str(e)}")


@router.get("/smart-paste/{session_id}", response_model=SmartPasteResponse)
async def smart_paste(
    session_id: str,
    query: str = Query(default=None, description="Optional: Focus on specific topic"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of memories to include"),
    service: SessionService = Depends(get_session_service),
    embedding_svc = Depends(get_embedding_service)
):
    """
    Smart Paste: Get memories from session in formatted text.

    This is the main feature for injecting context into conversations.

    By default, returns the most recent memories. If query is provided,
    uses semantic search to find the most relevant memories.

    Args:
        session_id: Session ID
        query: Optional search query for context-aware paste
        limit: Number of memories to include (default: 10)

    Returns:
        Formatted text ready to paste

    Examples:
        - No query: Returns last 10 memories (chronological)
        - With query "authentication": Returns 10 most relevant memories about auth
    """
    try:
        # Get session info
        session = await service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get memories (semantic search if query provided, otherwise recent)
        if query:
            # Semantic search - get most relevant memories
            try:
                query_embedding = await embedding_svc.create_embedding(query)
                results = await service.vector_search_memories(
                    session_id=session_id,
                    query_embedding=query_embedding,
                    match_threshold=0.3,
                    limit=limit
                )
                # Extract just the memory data
                memories = [{"processed_text": r["processed_text"]} for r in results]
            except Exception as e:
                import logging
                logging.warning(f"Semantic search failed in smart paste: {e}")
                # Fallback to recent memories
                result = await service.get_session_memories(session_id, limit=limit)
                memories = result["memories"]
        else:
            # Default: most recent memories
            result = await service.get_session_memories(session_id, limit=limit)
            memories = result["memories"]

        # Format for pasting
        if not memories:
            formatted_text = f"[Session Context: {session['name']} {session['icon']}]\n\nNo memories yet.\n\n[End Session Context]"
        else:
            # Header with query info
            if query:
                header = f"[Session Context: {session['name']} {session['icon']} - Filtered by: \"{query}\"]\n\nRelevant Context:\n\n"
            else:
                header = f"[Session Context: {session['name']} {session['icon']}]\n\nRecent History:\n\n"

            memory_texts = []
            for idx, memory in enumerate(memories, start=1):
                memory_texts.append(f"{idx}. {memory['processed_text']}")

            footer = "\n\n[End Session Context]"

            formatted_text = header + "\n\n".join(memory_texts) + footer

        return SmartPasteResponse(
            formatted_text=formatted_text,
            memory_count=len(memories),
            session_name=session["name"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Smart paste failed: {str(e)}")


# ============================================================================
# Session Memories CRUD
# ============================================================================

@router.get("/sessions/{session_id}/memories", response_model=MemoriesListResponse)
async def get_session_memories(
    session_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    service: SessionService = Depends(get_session_service)
):
    """
    Get memories for a session with pagination.

    Args:
        session_id: Session ID
        limit: Number of memories to return
        offset: Pagination offset

    Returns:
        List of memories with total count
    """
    try:
        result = await service.get_session_memories(session_id, limit, offset)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memories/{memory_id}", response_model=DeleteResponse)
async def delete_memory(
    memory_id: str,
    service: SessionService = Depends(get_session_service)
):
    """
    Delete a specific memory.

    Args:
        memory_id: Memory ID

    Returns:
        Deletion confirmation
    """
    try:
        await service.delete_memory(memory_id)
        return DeleteResponse(status="deleted", id=memory_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Personal Memory (Mem0)
# ============================================================================

@router.post("/memory/add", response_model=PersonalMemoryResponse)
async def add_personal_memory(request: PersonalMemoryRequest):
    """
    Add to personal memory (Mem0).

    This stores long-term user preferences and facts.

    Args:
        request: Text and user ID

    Returns:
        Confirmation message
    """
    try:
        await mem0_service.add_memory(request.text, request.user_id)

        return PersonalMemoryResponse(
            status="added",
            message="Added to personal memory"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add memory: {str(e)}")


@router.get("/memory/{user_id}", response_model=PersonalMemoriesResponse)
async def get_personal_memories(user_id: str):
    """
    Get all personal memories for a user (Mem0).

    Args:
        user_id: User ID

    Returns:
        List of personal memories
    """
    try:
        memories_data = await mem0_service.get_memories(user_id)

        # Transform Mem0 response to our model
        memories = []
        if isinstance(memories_data, list):
            for mem in memories_data:
                memories.append(PersonalMemory(
                    id=mem.get("id", ""),
                    text=mem.get("memory", mem.get("text", "")),
                    category=mem.get("category", None)
                ))

        return PersonalMemoriesResponse(memories=memories)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memories: {str(e)}")


# ============================================================================
# Search
# ============================================================================

@router.get("/search/{session_id}", response_model=SearchResponse)
async def search_session(
    session_id: str,
    query: str = Query(..., min_length=1),
    mode: str = Query(default="vector", regex="^(vector|text)$"),
    limit: int = Query(default=10, ge=1, le=50),
    service: SessionService = Depends(get_session_service),
    embedding_svc = Depends(get_embedding_service)
):
    """
    Search in session memories using vector (semantic) or text search.

    Args:
        session_id: Session ID
        query: Search query
        mode: Search mode - "vector" (semantic, default) or "text" (keyword)
        limit: Maximum number of results

    Returns:
        Search results with relevance scores
    """
    try:
        if mode == "vector":
            # Semantic search using embeddings
            try:
                # Generate query embedding
                query_embedding = await embedding_svc.create_embedding(query)

                # Vector search
                results = await service.vector_search_memories(
                    session_id=session_id,
                    query_embedding=query_embedding,
                    match_threshold=0.3,  # Lower threshold for broader results
                    limit=limit
                )
            except Exception as e:
                import logging
                logging.warning(f"Vector search failed, falling back to text search: {e}")
                # Fallback to text search if vector search fails
                results = await service.search_memories(session_id, query)
        else:
            # Traditional text search
            results = await service.search_memories(session_id, query)

        # Transform to response model
        search_results = [
            SearchResult(
                id=r["id"],
                processed_text=r["processed_text"],
                relevance_score=r["relevance_score"]
            )
            for r in results
        ]

        return SearchResponse(
            results=search_results,
            total=len(search_results)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
