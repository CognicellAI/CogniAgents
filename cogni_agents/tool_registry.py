import importlib.util
import inspect
import logging
import os
from typing import Any, Callable, Dict, List, Optional

from .config_loader import get_custom_tool_configs, get_mcp_server_configs
from pydantic_ai.mcp import MCPServerStreamableHTTP, MCPServerSSE, MCPServerStdio

logger = logging.getLogger(__name__)

_tool_registry: Dict[str, Callable[..., Any]] = {}
_tools_loaded = False
_mcp_servers: Dict[str, Any] = {}
_mcp_servers_loaded = False


def load_tools():
    """Loads custom tools from the configuration file."""
    global _tools_loaded
    if _tools_loaded:
        return

    logger.info("Loading tools...")
    custom_tool_paths = get_custom_tool_configs()

    for tool_name, import_path in custom_tool_paths.items():
        try:
            if ":" not in import_path:
                raise ValueError(
                    f"Invalid import path for tool '{tool_name}': '{import_path}'. "
                    "Format must be 'path.to.module:function_name'."
                )

            module_path, function_name = import_path.split(":", 1)
            module = importlib.import_module(module_path)
            tool_function = getattr(module, function_name)

            if not callable(tool_function):
                raise TypeError(
                    f"The object '{function_name}' from '{module_path}' is not a callable function."
                )

            _tool_registry[tool_name] = tool_function
            logger.debug(f"Successfully loaded and registered tool '{tool_name}' from '{import_path}'.")

        except (ValueError, ModuleNotFoundError, AttributeError, TypeError) as e:
            logger.error(f"Failed to load tool '{tool_name}' from '{import_path}': {e}")
            # Decide if you want to raise the error or just log it.
            # For now, we log and continue to allow other tools to load.
            continue

    _tools_loaded = True
    logger.info(f"Successfully loaded {len(_tool_registry)} custom tools.")


def load_mcp_servers():
    """Loads MCP servers from the configuration file."""
    global _mcp_servers_loaded
    if _mcp_servers_loaded:
        return

    logger.info("Loading MCP servers...")
    mcp_server_configs = get_mcp_server_configs()

    for server_name, config in mcp_server_configs.items():
        try:
            server_type = config.get("type")
            if server_type == "streamable-http":
                url = config.get("url")
                if not url:
                    logger.error(f"MCP server '{server_name}' of type 'streamable-http' is missing required 'url' parameter.")
                    continue
                _mcp_servers[server_name] = MCPServerStreamableHTTP(url=url)
            elif server_type == "sse":
                url = config.get("url")
                if not url:
                    logger.error(f"MCP server '{server_name}' of type 'sse' is missing required 'url' parameter.")
                    continue
                _mcp_servers[server_name] = MCPServerSSE(url=url)
            elif server_type == "stdio":
                command = config.get("command")
                args = config.get("args")
                if not command or not args:
                    logger.error(f"MCP server '{server_name}' of type 'stdio' is missing required 'command' or 'args' parameters.")
                    continue
                _mcp_servers[server_name] = MCPServerStdio(command=command, args=args)
            else:
                logger.error(f"Unknown MCP server type '{server_type}' for server '{server_name}'.")
        except Exception as e:
            logger.error(f"Failed to load MCP server '{server_name}': {e}")

    _mcp_servers_loaded = True
    logger.info(f"Successfully loaded {len(_mcp_servers)} MCP servers.")

def get_tool(tool_name: str) -> Optional[Callable[..., Any]]:
    """Retrieves a tool from the registry by name."""
    if not _tools_loaded:
        load_tools()
    return _tool_registry.get(tool_name)

def get_mcp_server(server_name: str) -> Optional[Any]:
    """Retrieves an MCP server from the registry by name."""
    if not _mcp_servers_loaded:
        load_mcp_servers()
    return _mcp_servers.get(server_name)

def get_tools_and_toolsets(tool_names: List[str], toolset_names: List[str]) -> tuple[List[Callable[..., Any]], List[Any]]:
    """Retrieves a list of tools and a list of toolsets from the registry by name."""
    if not _tools_loaded:
        load_tools()
    
    tools = []
    for tool_name in tool_names:
        tool = get_tool(tool_name)
        if tool:
            tools.append(tool)
        else:
            logger.warning(f"Tool '{tool_name}' not found in registry.")

    toolsets = []
    for toolset_name in toolset_names:
        toolset = get_mcp_server(toolset_name)
        if toolset:
            toolsets.append(toolset)
        else:
            logger.warning(f"Toolset '{toolset_name}' not found in registry.")

    return tools, toolsets


def reload_tools():
    """Reloads all tools and MCP servers from the configuration file."""
    global _tool_registry, _tools_loaded, _mcp_servers, _mcp_servers_loaded
    logger.debug("Reloading tools...")
    _tool_registry = {}
    _tools_loaded = False
    _mcp_servers = {}
    _mcp_servers_loaded = False

_mcp_servers: Dict[str, Any] = {}
_mcp_servers_loaded = False
