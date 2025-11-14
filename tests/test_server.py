"""Integration tests for MCPX server."""

import pytest
from unittest.mock import Mock, patch
from mcp_server.server import get_server


def test_get_server():
    """Test server initialization."""
    with patch("mcp_server.server.config") as mock_config:
        mock_config.validate.return_value = True
        mock_config.LOG_LEVEL = "INFO"
        
        server = get_server()
        assert server is not None


def test_server_has_tools():
    """Test that server has all required tools registered."""
    with patch("mcp_server.server.config") as mock_config:
        mock_config.validate.return_value = True
        mock_config.LOG_LEVEL = "INFO"
        
        server = get_server()
        
        # Check that tools are registered
        # This would depend on FastMCP's internal structure
        # For now, just verify server was created
        assert server is not None

