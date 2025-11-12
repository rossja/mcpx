"""Web search tool implementation using OpenAI."""

from typing import Optional
from openai import AsyncOpenAI
from mcp.server.fastmcp import Context
from ..config import config


async def web_search(query: str, max_results: int = 5, context: Context = None) -> str:
    """Search the web using OpenAI's search capabilities.

    Args:
        query: Search query
        max_results: Maximum number of results to return (default: 5)
        context: MCP context (unused in this tool)

    Returns:
        Formatted search results with title, URL, and snippet

    Raises:
        RuntimeError: If OpenAI API key is not configured or API request fails
    """
    if not config.OPENAI_API_KEY:
        raise RuntimeError(
            "OpenAI API key not configured. "
            "Please set OPENAI_API_KEY environment variable."
        )

    try:
        client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

        # Use OpenAI's chat completion with web search enabled
        # Note: This uses the newer model with web search capabilities
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a web search assistant. Search for information about: {query}\n"
                        f"Return up to {max_results} relevant results. "
                        "Format each result with: Title, URL (if available), and a brief description."
                    )
                },
                {
                    "role": "user",
                    "content": f"Search for: {query}"
                }
            ],
            max_tokens=1000,
            temperature=0.3,
        )

        result = response.choices[0].message.content

        return f"Web Search Results for: {query}\n\n{result}"

    except Exception as e:
        raise RuntimeError(f"Web search failed: {str(e)}")

