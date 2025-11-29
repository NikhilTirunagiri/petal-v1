"""Supabase database client initialization."""

from supabase import create_client, Client
from app.config import settings


class Database:
    """Supabase database client wrapper."""

    def __init__(self):
        """Initialize Supabase client."""
        self.client: Client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_anon_key
        )

    def get_client(self) -> Client:
        """Get the Supabase client instance."""
        return self.client


# Global database instance
db = Database()


def get_db() -> Client:
    """Dependency function to get database client."""
    return db.get_client()
