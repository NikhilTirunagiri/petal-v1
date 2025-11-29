"""Claude API service for text processing and summarization."""

from anthropic import Anthropic
from app.config import settings


class ClaudeService:
    """Service for interacting with Claude API."""

    def __init__(self):
        """Initialize Anthropic client."""
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"

    async def process_text(self, text: str) -> str:
        """
        Process and summarize text using Claude.

        Args:
            text: The original text to process

        Returns:
            Processed/summarized text
        """
        prompt = f"""You are summarizing content for a knowledge management system. Create a dense, information-rich summary optimized for future retrieval and context reconstruction.
        
CRITICAL REQUIREMENTS:
- Preserve ALL technical specifics: APIs, libraries, versions, commands, file paths
- Keep code snippets verbatim (use ```language blocks)
- Maintain exact terminology and proper nouns
- Flag decisions, problems, and solutions explicitly
- Structure for scannability

FORMAT:
Use natural paragraphs with these elements when present:
- **Topic/Title** at start if identifiable
- Technical details inline with context
- Code blocks preserved exactly
- Action items with clear subjects ("Need to...", "Should...")
- Key decisions/conclusions

TONE: Dense technical prose, no fluff, no meta-commentary like "this text discusses..."

INPUT TEXT:
{text}

SUMMARY:"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract the text content from the response
            processed_text = message.content[0].text
            return processed_text.strip()

        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")

    async def generate_session_description(self, memories: list[str]) -> str:
        """
        Generate a concise description of a session based on its memories.

        Args:
            memories: List of processed memory texts

        Returns:
            A 1-2 sentence description of what this session is about
        """
        if not memories:
            return "No memories yet in this session."

        # Combine memories (limit to prevent token overflow)
        memory_text = "\n\n".join(memories[:20])  # Use max 20 most recent memories

        prompt = f"""You are analyzing a user's session memories to create a concise session description.

Based on the memories below, generate a 1-2 sentence description that captures the main theme or purpose of this session.

Be specific and mention key topics, technologies, or goals if clear.

MEMORIES:
{memory_text}

DESCRIPTION (1-2 sentences only):"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            description = message.content[0].text
            return description.strip()

        except Exception as e:
            raise Exception(f"Claude API error generating description: {str(e)}")

    async def generate_tags(self, text: str) -> list[str]:
        """
        Generate relevant tags for a memory based on its content.

        Args:
            text: The memory text

        Returns:
            List of tags (e.g., ["python", "api", "optimization"])
        """
        prompt = f"""Extract 2-5 relevant tags from this text for categorization.

Tags should be:
- Single words or short phrases (1-2 words)
- Lowercase
- Technical terms, technologies, concepts, or topics
- No generic words like "text", "information", etc.

Return ONLY the tags as a comma-separated list, nothing else.

TEXT:
{text[:500]}

TAGS:"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=50,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            tags_text = message.content[0].text.strip()
            # Parse comma-separated tags
            tags = [tag.strip().lower().replace("#", "") for tag in tags_text.split(",")]
            # Filter out empty tags and limit to 5
            tags = [tag for tag in tags if tag and len(tag) > 1][:5]
            return tags

        except Exception as e:
            # Return empty list if tagging fails (non-critical)
            import logging
            logging.warning(f"Failed to generate tags: {e}")
            return []

    async def handle_chat_message(
        self,
        message: str,
        session_id: str,
        user_id: str,
        search_scope: str = "current"
    ) -> dict:
        """
        Process a chat message and determine intent/action.

        Args:
            message: User's chat message
            session_id: Current session ID
            user_id: User ID
            search_scope: "current" or "all"

        Returns:
            Dict with intent, response, and any actions to take
        """
        prompt = f"""You are Petal, a personal memory assistant. Analyze this user message and determine the intent.

USER MESSAGE: "{message}"

Respond ONLY with a JSON object (no markdown, no explanation) in this format:
{{
    "intent": "remember|search|delete|create_session|switch_session|show_memories|general",
    "content": "extracted content or search query",
    "tags": ["tag1", "tag2"],
    "response": "natural language response to user"
}}

INTENTS:
- "remember": User wants to save something (keywords: "remember", "note", "save", "store")
- "search": User is asking a question or wants to find something
- "delete": User wants to remove a memory
- "create_session": User wants to create a new session (keywords: "create session", "new session")
- "switch_session": User wants to switch sessions
- "show_memories": User wants to see recent memories
- "general": Chitchat or unclear intent

JSON:"""

        try:
            response_msg = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            import json
            result = json.loads(response_msg.content[0].text.strip())
            return result

        except Exception as e:
            # Fallback response
            return {
                "intent": "general",
                "content": message,
                "tags": [],
                "response": "I'm sorry, I didn't understand that. Try asking me to remember something or search for information."
            }


# Global Claude service instance
claude_service = ClaudeService()
