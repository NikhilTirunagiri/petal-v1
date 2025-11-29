"""Mem0 API service for personal memory management."""

from mem0 import MemoryClient
from app.config import settings
from typing import List, Dict, Any


class Mem0Service:
    """Service for interacting with Mem0 API."""

    def __init__(self):
        """Initialize Mem0 client."""
        self.client = MemoryClient(api_key=settings.mem0_api_key)

    async def add_memory(self, text: str, user_id: str) -> Dict[str, Any]:
        """
        Add a memory to Mem0.

        Args:
            text: The memory text to add
            user_id: The user ID

        Returns:
            Response from Mem0 API
        """
        try:
            response = self.client.add(
                messages=[{"role": "user", "content": text}],
                user_id=user_id
            )
            return response

        except Exception as e:
            raise Exception(f"Mem0 API error: {str(e)}")

    async def get_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all memories for a user from Mem0.

        Args:
            user_id: The user ID

        Returns:
            List of memories
        """
        try:
            response = self.client.get_all(
                filters={"user_id": user_id}
            )
            return response

        except Exception as e:
            raise Exception(f"Mem0 API error: {str(e)}")

    async def search_memories(self, query: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Search memories for a user.

        Args:
            query: Search query
            user_id: The user ID

        Returns:
            List of matching memories
        """
        try:
            response = self.client.search(
                query=query,
                user_id=user_id
            )
            return response

        except Exception as e:
            raise Exception(f"Mem0 API error: {str(e)}")


# Global Mem0 service instance
mem0_service = Mem0Service()
