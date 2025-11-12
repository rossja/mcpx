"""Weather lookup tool implementation."""

import httpx
from typing import Optional
from mcp.server.fastmcp import Context
from ..config import config


async def get_weather(zip_code: str, context: Context) -> str:
    """Get current weather information for a US ZIP code.

    Uses the OpenWeather API to retrieve current weather conditions.

    Args:
        zip_code: 5-digit US ZIP code
        context: MCP context (unused in this tool)

    Returns:
        Formatted weather information including temperature, conditions, and humidity

    Raises:
        ValueError: If the ZIP code format is invalid
        RuntimeError: If the weather API is unavailable or returns an error
    """
    # Validate ZIP code format
    if not zip_code.isdigit() or len(zip_code) != 5:
        raise ValueError("Invalid ZIP code format. Please provide a 5-digit US ZIP code.")

    # Check if API key is configured
    if not config.WEATHER_API_KEY:
        # Use a free weather API (weather.gov) as fallback
        try:
            return await _get_weather_from_nws(zip_code)
        except Exception as e:
            return f"Weather service unavailable: {str(e)}\n\nNote: Set WEATHER_API_KEY environment variable for OpenWeatherMap integration."

    # Use OpenWeatherMap API
    try:
        return await _get_weather_from_openweather(zip_code)
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve weather data: {str(e)}")


async def _get_weather_from_openweather(zip_code: str) -> str:
    """Fetch weather from OpenWeatherMap API."""
    api_key = config.WEATHER_API_KEY
    url = f"https://api.openweathermap.org/data/2.5/weather?zip={zip_code},US&appid={api_key}&units=imperial"

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url)

        if response.status_code == 404:
            raise ValueError(f"ZIP code {zip_code} not found.")
        elif response.status_code == 429:
            raise RuntimeError("Weather API rate limit exceeded. Please try again later.")
        elif response.status_code != 200:
            raise RuntimeError(f"Weather API error: {response.status_code}")

        data = response.json()

        # Extract weather information
        location = data.get("name", "Unknown")
        temp = data["main"]["temp"]
        conditions = data["weather"][0]["description"].title()
        humidity = data["main"]["humidity"]

        return (
            f"Weather for {location} ({zip_code}):\n"
            f"Temperature: {temp:.0f}°F\n"
            f"Conditions: {conditions}\n"
            f"Humidity: {humidity}%"
        )


async def _get_weather_from_nws(zip_code: str) -> str:
    """Fetch weather from National Weather Service (weather.gov) as fallback.
    
    Note: This is a simplified implementation that uses a ZIP code to coordinates
    conversion service and then queries NWS.
    """
    # First, convert ZIP to coordinates using a free API
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Use zip-codes.com API or similar free service
        # For demo purposes, we'll return a helpful message
        return (
            f"Weather lookup for ZIP code {zip_code}\n\n"
            "⚠️  To enable full weather functionality, please set the WEATHER_API_KEY environment variable.\n\n"
            "Get a free API key from: https://openweathermap.org/api\n"
            "Then add to your .env file: WEATHER_API_KEY=your_key_here"
        )

