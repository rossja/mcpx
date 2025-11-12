"""Unit tests for MCPX tools."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.tools.echo import echo
from src.tools.weather import get_weather
from src.tools.web_search import web_search
from src.tools.ip_lookup import get_source_ip
from src.tools.request_info import get_request_info


@pytest.mark.asyncio
async def test_echo():
    """Test echo tool."""
    context = Mock()
    result = await echo("Hello, World!", context)
    assert result == "Hello, World!"


@pytest.mark.asyncio
async def test_echo_empty_string():
    """Test echo tool with empty string."""
    context = Mock()
    result = await echo("", context)
    assert result == ""


@pytest.mark.asyncio
async def test_weather_invalid_zip():
    """Test weather tool with invalid ZIP code."""
    context = Mock()
    
    # Test non-numeric ZIP
    with pytest.raises(ValueError, match="Invalid ZIP code format"):
        await get_weather("abcde", context)
    
    # Test wrong length
    with pytest.raises(ValueError, match="Invalid ZIP code format"):
        await get_weather("123", context)


@pytest.mark.asyncio
async def test_weather_no_api_key():
    """Test weather tool without API key configured."""
    context = Mock()
    
    with patch("src.tools.weather.config") as mock_config:
        mock_config.WEATHER_API_KEY = None
        result = await get_weather("10001", context)
        assert "WEATHER_API_KEY" in result or "unavailable" in result.lower()


@pytest.mark.asyncio
async def test_web_search_no_api_key():
    """Test web search without API key."""
    context = Mock()
    
    with patch("src.tools.web_search.config") as mock_config:
        mock_config.OPENAI_API_KEY = None
        with pytest.raises(RuntimeError, match="OpenAI API key not configured"):
            await web_search("test query", 5, context)


@pytest.mark.asyncio
async def test_get_source_ip_no_context():
    """Test source IP lookup without request context."""
    context = Mock()
    context.request_context = None
    context._request = None
    
    with patch("src.tools.ip_lookup._get_request_from_context", return_value=None):
        result = await get_source_ip(context)
        assert "Unable to determine" in result


@pytest.mark.asyncio
async def test_get_source_ip_with_forwarded_header():
    """Test source IP lookup with X-Forwarded-For header."""
    mock_request = Mock()
    mock_request.headers.get = lambda key: "203.0.113.42, 10.0.0.1" if key == "x-forwarded-for" else None
    mock_request.client = Mock(host="10.0.0.1")
    
    context = Mock()
    context.request_context = {"request": mock_request}
    
    result = await get_source_ip(context)
    assert "203.0.113.42" in result
    assert "proxy" in result.lower()


@pytest.mark.asyncio
async def test_get_request_info_no_context():
    """Test request info without context."""
    context = Mock()
    context.request_context = None
    
    with patch("src.tools.request_info._get_request_from_context", return_value=None):
        result = await get_request_info(context)
        assert "Unable to retrieve" in result


@pytest.mark.asyncio
async def test_get_request_info_with_request():
    """Test request info with valid request."""
    mock_request = Mock()
    mock_request.method = "POST"
    mock_request.url = Mock()
    mock_request.url.path = "/test"
    mock_request.url.query = "param=value"
    mock_request.scope = {"scheme": "https", "http_version": "1.1", "server": ("mcpx.lol", 443)}
    mock_request.client = Mock(host="203.0.113.42", port=54321)
    
    # Mock headers as a dict-like object
    mock_headers = Mock()
    mock_headers.get = lambda key, default=None: {
        "user-agent": "Test/1.0",
        "host": "mcpx.lol",
        "x-forwarded-for": None,
        "x-real-ip": None
    }.get(key.lower(), default)
    mock_headers.items = lambda: [("user-agent", "Test/1.0"), ("host", "mcpx.lol")]
    mock_request.headers = mock_headers
    
    context = Mock()
    
    with patch("src.tools.request_info._get_request_from_context", return_value=mock_request):
        result = await get_request_info(context)
        assert "POST" in result
        assert "/test" in result
        assert "203.0.113.42" in result

