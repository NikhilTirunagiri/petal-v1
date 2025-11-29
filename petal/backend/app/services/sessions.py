"""Session management service."""

from supabase import Client
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing sessions and memories in Supabase."""

    def __init__(self, db_client: Client):
        """Initialize with Supabase client."""
        self.db = db_client

    # ========================================================================
    # Session CRUD Operations
    # ========================================================================

    async def create_session(
        self,
        user_id: str,
        name: str,
        icon: str = "📁",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new session."""
        try:
            data = {
                "user_id": user_id,
                "name": name,
                "icon": icon,
                "description": description
            }

            response = self.db.table("sessions").insert(data).execute()
            return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            raise Exception(f"Failed to create session: {str(e)}")

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        try:
            response = self.db.table("sessions")\
                .select("id, user_id, name, icon, created_at")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error fetching user sessions: {str(e)}")
            raise Exception(f"Failed to fetch sessions: {str(e)}")

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a single session by ID with memory count."""
        try:
            # Optimized: Get both session and count in a single query using aggregation
            # This eliminates the N+1 problem by using PostgreSQL's COUNT in a subquery
            response = self.db.table("sessions")\
                .select("*, session_memories(id)")\
                .eq("id", session_id)\
                .limit(1)\
                .execute()

            if not response.data:
                return None

            session = response.data[0]

            # Count memories from the joined data
            memories = session.pop("session_memories", [])
            session["memory_count"] = len(memories) if memories else 0

            return session

        except Exception as e:
            logger.error(f"Error fetching session: {str(e)}")
            raise Exception(f"Failed to fetch session: {str(e)}")

    async def update_session(
        self,
        session_id: str,
        name: Optional[str] = None,
        icon: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update a session."""
        try:
            data = {}
            if name is not None:
                data["name"] = name
            if icon is not None:
                data["icon"] = icon
            if description is not None:
                data["description"] = description

            if not data:
                return None

            response = self.db.table("sessions")\
                .update(data)\
                .eq("id", session_id)\
                .execute()

            return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Error updating session: {str(e)}")
            raise Exception(f"Failed to update session: {str(e)}")

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session (cascades to memories)."""
        try:
            response = self.db.table("sessions")\
                .delete()\
                .eq("id", session_id)\
                .execute()

            return True

        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
            raise Exception(f"Failed to delete session: {str(e)}")

    # ========================================================================
    # Memory Operations
    # ========================================================================

    async def save_memory(
        self,
        session_id: str,
        user_id: str,
        original_text: str,
        processed_text: str,
        source: Optional[str] = None,
        embedding: Optional[list] = None
    ) -> Dict[str, Any]:
        """Save a memory to a session with optional embedding."""
        try:
            data = {
                "session_id": session_id,
                "user_id": user_id,
                "original_text": original_text,
                "processed_text": processed_text,
                "source": source,
                "metadata": {}
            }

            # Add embedding if provided
            if embedding:
                # Convert to PostgreSQL vector format
                data["embedding"] = embedding

            response = self.db.table("session_memories")\
                .insert(data)\
                .execute()

            return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Error saving memory: {str(e)}")
            raise Exception(f"Failed to save memory: {str(e)}")

    async def get_session_memories(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get memories for a session with pagination."""
        try:
            # Get memories
            response = self.db.table("session_memories")\
                .select("id, processed_text, created_at")\
                .eq("session_id", session_id)\
                .order("created_at", desc=False)\
                .range(offset, offset + limit - 1)\
                .execute()

            # Get total count
            count_response = self.db.table("session_memories")\
                .select("id", count="exact")\
                .eq("session_id", session_id)\
                .execute()

            return {
                "memories": response.data if response.data else [],
                "total": count_response.count if count_response.count else 0
            }

        except Exception as e:
            logger.error(f"Error fetching memories: {str(e)}")
            raise Exception(f"Failed to fetch memories: {str(e)}")

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory."""
        try:
            response = self.db.table("session_memories")\
                .delete()\
                .eq("id", memory_id)\
                .execute()

            return True

        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            raise Exception(f"Failed to delete memory: {str(e)}")

    async def search_memories(
        self,
        session_id: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """Search memories in a session using simple text matching."""
        try:
            # Get all memories in session
            response = self.db.table("session_memories")\
                .select("id, processed_text")\
                .eq("session_id", session_id)\
                .execute()

            # Filter and score based on query
            results = []
            query_lower = query.lower()
            query_words = query_lower.split()

            for memory in (response.data if response.data else []):
                text_lower = memory["processed_text"].lower()

                # Check if any query words are in the text
                matches = sum(1 for word in query_words if word in text_lower)

                if matches > 0:
                    # Simple relevance: percentage of query words found
                    relevance = matches / len(query_words) if query_words else 0

                    results.append({
                        "id": memory["id"],
                        "processed_text": memory["processed_text"],
                        "relevance_score": relevance
                    })

            # Sort by relevance
            results.sort(key=lambda x: x["relevance_score"], reverse=True)

            return results

        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            raise Exception(f"Failed to search memories: {str(e)}")

    # ========================================================================
    # Vector Search Operations
    # ========================================================================

    async def vector_search_memories(
        self,
        session_id: str,
        query_embedding: list,
        match_threshold: float = 0.5,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search memories using vector similarity (semantic search).

        Args:
            session_id: Session ID to search within
            query_embedding: Embedding vector of the search query
            match_threshold: Minimum similarity score (0-1)
            limit: Maximum number of results

        Returns:
            List of memories with similarity scores
        """
        try:
            # Call the Postgres function we created
            response = self.db.rpc('match_session_memories', {
                'query_embedding': query_embedding,
                'p_session_id': session_id,
                'match_threshold': match_threshold,
                'match_count': limit
            }).execute()

            results = []
            for memory in (response.data if response.data else []):
                results.append({
                    "id": memory["id"],
                    "processed_text": memory["processed_text"],
                    "created_at": memory["created_at"],
                    "relevance_score": memory["similarity"]
                })

            return results

        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            raise Exception(f"Failed to perform vector search: {str(e)}")

    async def vector_search_all_sessions(
        self,
        user_id: str,
        query_embedding: list,
        match_threshold: float = 0.5,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search memories across all user sessions using vector similarity.

        Args:
            user_id: User ID
            query_embedding: Embedding vector of the search query
            match_threshold: Minimum similarity score (0-1)
            limit: Maximum number of results

        Returns:
            List of memories from all sessions with similarity scores
        """
        try:
            # Call the Postgres function
            response = self.db.rpc('match_user_memories', {
                'query_embedding': query_embedding,
                'p_user_id': user_id,
                'match_threshold': match_threshold,
                'match_count': limit
            }).execute()

            results = []
            for memory in (response.data if response.data else []):
                results.append({
                    "id": memory["id"],
                    "session_id": memory["session_id"],
                    "session_name": memory["session_name"],
                    "processed_text": memory["processed_text"],
                    "created_at": memory["created_at"],
                    "relevance_score": memory["similarity"]
                })

            return results

        except Exception as e:
            logger.error(f"Error in cross-session vector search: {str(e)}")
            raise Exception(f"Failed to perform cross-session search: {str(e)}")

    async def find_duplicate_memories(
        self,
        session_id: str,
        embedding: list,
        similarity_threshold: float = 0.95
    ) -> List[Dict[str, Any]]:
        """
        Find similar/duplicate memories in a session.

        Useful to detect if user is copying the same content multiple times.

        Args:
            session_id: Session ID
            embedding: Embedding to check against
            similarity_threshold: Minimum similarity to consider duplicate (default 0.95)

        Returns:
            List of similar memories
        """
        try:
            response = self.db.rpc('find_similar_memories', {
                'check_embedding': embedding,
                'p_session_id': session_id,
                'similarity_threshold': similarity_threshold,
                'max_results': 5
            }).execute()

            results = []
            for memory in (response.data if response.data else []):
                results.append({
                    "id": memory["id"],
                    "processed_text": memory["processed_text"],
                    "similarity": memory["similarity"]
                })

            return results

        except Exception as e:
            logger.error(f"Error finding duplicates: {str(e)}")
            # Don't fail the whole operation if duplicate detection fails
            return []
