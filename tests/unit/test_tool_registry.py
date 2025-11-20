import pytest
from unittest.mock import patch, mock_open

from cogni_agents.tool_registry import get_tool, get_tools_and_toolsets, load_tools, reload_tools, load_mcp_servers

# A simple dummy function to be used as a tool
def dummy_tool():
    return "dummy_tool_output"

class TestToolRegistry:

    @pytest.fixture(autouse=True)
    def reset_tool_registry(self):
        """Ensures the tool registry is reset before and after each test."""
        reload_tools()
        yield
        reload_tools()

    @patch("cogni_agents.tool_registry.get_custom_tool_configs")
    def test_load_tools_successfully(self, mock_get_configs):
        mock_get_configs.return_value = {
            "my_tool": "tests.unit.test_tool_registry:dummy_tool"
        }

        load_tools()
        tool = get_tool("my_tool")
        assert tool is not None
        assert callable(tool)
        assert tool() == "dummy_tool_output"

    @patch("cogni_agents.tool_registry.get_custom_tool_configs")
    def test_get_tools_and_toolsets_returns_correct_list(self, mock_get_configs):
        mock_get_configs.return_value = {
            "tool1": "tests.unit.test_tool_registry:dummy_tool",
            "tool2": "tests.unit.test_tool_registry:dummy_tool",
        }

        tools, toolsets = get_tools_and_toolsets(["tool1", "tool2"], [])
        assert len(tools) == 2
        assert all(callable(t) for t in tools)
        assert len(toolsets) == 0

    @patch("cogni_agents.config_loader._load_config", return_value={})
    @patch("cogni_agents.tool_registry.get_mcp_server_configs")
    def test_load_mcp_servers_successfully(self, mock_get_mcp_configs, mock_load_config):
        mock_get_mcp_configs.return_value = {
            "my_mcp_server": {
                "type": "streamable-http",
                "url": "http://localhost:8000/mcp",
            }
        }

        load_mcp_servers()
        tools, toolsets = get_tools_and_toolsets([], ["my_mcp_server"])
        assert len(tools) == 0
        assert len(toolsets) == 1
        mock_get_mcp_configs.return_value = {
            "my_mcp_server": {
                "type": "streamable-http",
                "url": "http://localhost:8000/mcp",
            }
        }

        load_mcp_servers()
        tools, toolsets = get_tools_and_toolsets([], ["my_mcp_server"])
        assert len(tools) == 0
        assert len(toolsets) == 1

    @patch("cogni_agents.tool_registry.get_custom_tool_configs")
    def test_get_tool_not_found_returns_none(self, mock_get_configs):
        mock_get_configs.return_value = {}
        tool = get_tool("non_existent_tool")
        assert tool is None

    @patch("cogni_agents.config_loader._load_config", return_value={})
    def test_reload_tools_clears_registry(self, mock_load_config):
        # This test needs to be carefully written to not interfere with others.
        # It relies on the fixture for setup and teardown.
        # 1. Load something into the registry
        with patch("cogni_agents.tool_registry.get_custom_tool_configs") as mock_get_configs:
            mock_get_configs.return_value = {"temp_tool": "tests.unit.test_tool_registry:dummy_tool"}
            load_tools()
            assert get_tool("temp_tool") is not None

        # 2. Rreload should clear it
        reload_tools()
        assert get_tool("temp_tool") is None
