"""
Migration script to generate embeddings for existing memories.

Run this after:
1. Running supabase_migration_pgvector.sql
2. Adding OpenRouter API key to .env

Usage:
    python migrate_embeddings.py
"""

import asyncio
from app.database import db
from app.services.embeddings import embedding_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_embeddings():
    """Generate embeddings for all memories that don't have them."""

    logger.info("Starting embedding migration...")

    try:
        # Get all memories without embeddings
        response = db.get_client().table("session_memories")\
            .select("id, processed_text")\
            .is_("embedding", "null")\
            .execute()

        memories = response.data if response.data else []
        total = len(memories)

        if total == 0:
            logger.info("No memories need migration. All done!")
            return

        logger.info(f"Found {total} memories without embeddings")

        # Process in batches of 100
        batch_size = 100
        success_count = 0
        error_count = 0

        for i in range(0, total, batch_size):
            batch = memories[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}")

            for memory in batch:
                try:
                    # Generate embedding
                    embedding = await embedding_service.create_embedding(memory["processed_text"])

                    # Update memory with embedding
                    db.get_client().table("session_memories")\
                        .update({"embedding": embedding})\
                        .eq("id", memory["id"])\
                        .execute()

                    success_count += 1

                    if success_count % 10 == 0:
                        logger.info(f"Progress: {success_count}/{total} completed")

                except Exception as e:
                    logger.error(f"Failed to process memory {memory['id']}: {str(e)}")
                    error_count += 1
                    continue

            # Small delay between batches to avoid rate limits
            await asyncio.sleep(1)

        logger.info("="*50)
        logger.info(f"Migration complete!")
        logger.info(f"✓ Successful: {success_count}")
        logger.info(f"✗ Failed: {error_count}")
        logger.info(f"Total processed: {success_count + error_count}/{total}")
        logger.info("="*50)

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate_embeddings())
