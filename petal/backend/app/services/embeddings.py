"""OpenAI Embeddings service for vector search via OpenRouter."""

from openai import OpenAI
from app.config import settings
from typing import List
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using OpenRouter."""

    def __init__(self, embedding_cache=None):
        """Initialize OpenAI client configured for OpenRouter."""
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openai_api_key,  # OpenRouter API key
        )
        # Using text-embedding-3-small via OpenRouter
        # Dimensions: 1536
        # OpenRouter cost: Usually cheaper than direct OpenAI
        self.model = "openai/text-embedding-3-small"
        self.dimensions = 1536
        self.cache = embedding_cache

    async def create_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text (with caching).

        Args:
            text: The text to embed (max ~8K tokens)

        Returns:
            List of 1536 float values representing the embedding

        Raises:
            Exception: If OpenAI API call fails
        """
        try:
            # Truncate text if too long (8K tokens = ~6K words)
            max_chars = 30000  # Conservative limit
            if len(text) > max_chars:
                logger.warning(f"Text truncated from {len(text)} to {max_chars} chars")
                text = text[:max_chars]

            # Try cache first
            if self.cache:
                cached_embedding = self.cache.get_embedding(text)
                if cached_embedding:
                    logger.info(f"Using cached embedding for {len(text)} chars")
                    return cached_embedding

            # Cache miss - generate embedding via API
            logger.info(f"Calling OpenRouter API for {len(text)} chars...")
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )

            embedding = response.data[0].embedding

            logger.info(f"Generated embedding, {response.usage.total_tokens} tokens")

            # Save to cache
            if self.cache:
                self.cache.save_embedding(text, embedding)

            return embedding

        except Exception as e:
            logger.error(f"OpenAI embedding error: {str(e)}")
            raise Exception(f"Failed to generate embedding: {str(e)}")

    async def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a single API call.

        More efficient than calling create_embedding multiple times.

        Args:
            texts: List of texts to embed (max 2048 texts per batch)

        Returns:
            List of embedding vectors

        Raises:
            Exception: If OpenAI API call fails
        """
        try:
            if len(texts) > 2048:
                raise ValueError("Batch size cannot exceed 2048 texts")

            # Truncate each text if needed
            max_chars = 30000
            truncated_texts = [
                text[:max_chars] if len(text) > max_chars else text
                for text in texts
            ]

            # Generate embeddings
            response = self.client.embeddings.create(
                model=self.model,
                input=truncated_texts,
                encoding_format="float"
            )

            # Extract embeddings in order
            embeddings = [item.embedding for item in response.data]

            logger.info(f"Generated {len(embeddings)} embeddings, {response.usage.total_tokens} tokens")

            return embeddings

        except Exception as e:
            logger.error(f"OpenAI batch embedding error: {str(e)}")
            raise Exception(f"Failed to generate batch embeddings: {str(e)}")

    def get_embedding_dimensions(self) -> int:
        """Get the dimensionality of embeddings."""
        return self.dimensions


# Global embedding service instance
# Cache will be injected when importing
embedding_service = None  # Initialized in main.py
