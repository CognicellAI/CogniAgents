import yaml
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file at the start
# This ensures that OPENAI_BASE_URL and OPENAI_API_KEY are available
# for PydanticAI's OpenAIChatModel.
load_dotenv()

# Path to the configuration file
# Can be overridden by the COGNIA_CONFIG_PATH environment variable
_config_file_path: Optional[str] = None
_config: Optional[Dict[str, Any]] = None

def set_config_path(path: str):
    """
    Sets the path to the configuration file and triggers a full reload of all
    framework components (config, schemas, agents, workflows).

    This should be called before any other framework functions if using a
    non-default config path programmatically.
    """
    global _config_file_path
    if _config_file_path != path:
        _config_file_path = path
        reload_config()

def _get_current_config_path() -> str:
    """
    Determines the current configuration file path.

    The path must be specified either by calling `set_config_path()` programmatically
    or by setting the `COGNIA_CONFIG_PATH` environment variable.

    Raises:
        FileNotFoundError: If the configuration path is not specified.
    """
    path = _config_file_path or os.getenv("COGNIA_CONFIG_PATH")
    if not path:
        raise FileNotFoundError(
            "Configuration file path not specified. Please set it using "
            "set_config_path() or the COGNIA_CONFIG_PATH environment variable."
        )
    return path

def _load_config() -> Dict[str, Any]:
    """
    Loads the configuration from the YAML file.
    Caches the loaded configuration for subsequent calls.
    """
    global _config
    if _config is None:
        current_path = _get_current_config_path()
        try:
            with open(current_path, 'r') as f:
                _config = yaml.safe_load(f)
            if not isinstance(_config, dict):
                raise ValueError("Config file must contain a dictionary at its root.")
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at {current_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration: {e}")
    return _config

def get_global_llm_settings() -> Dict[str, Any]:
    """
    Retrieves the global LLM settings from the configuration.
    """
    config = _load_config()
    return config.get("global_llm_settings", {})

def get_agent_configs() -> List[Dict[str, Any]]:
    """
    Retrieves the list of agent configurations.
    """
    config = _load_config()
    agents = config.get("agents", [])
    if not isinstance(agents, list):
        raise ValueError("Agents configuration must be a list.")
    return agents

def get_custom_schema_configs() -> Dict[str, str]:
    """
    Retrieves the custom schema mapping from the configuration.
    Returns a dictionary mapping a schema name to its import path.
    """
    config = _load_config()
    return config.get("custom_schemas", {})

def get_mcp_server_configs() -> Dict[str, Dict[str, Any]]:
    """
    Retrieves the mcp server mapping from the configuration.
    Returns a dictionary mapping a mcp server name to its import path.
    """
    config = _load_config()
    return config.get("mcp_servers", {})

def get_custom_tool_configs() -> Dict[str, str]:
    """
    Retrieves the custom tool mapping from the configuration.
    Returns a dictionary mapping a tool name to its import path.
    """
    config = _load_config()
    return config.get("custom_tools", {})

def get_prompt_components() -> Dict[str, str]:
    """
    Retrieves the prompt components from the configuration.
    Returns a dictionary mapping a component name to its text content.
    """
    config = _load_config()
    return config.get("prompt_components", {})

def get_defaults() -> Dict[str, Any]:
    """
    Retrieves the default settings from the configuration.
    """
    config = _load_config()
    defaults = config.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ValueError("Defaults configuration must be a dictionary.")
    return defaults

def reload_config():
    """
    Forces a reload of the configuration from the file.
    This also triggers a reload of agents, workflows, and custom schemas.
    """
    global _config
    _config = None
    _load_config() # Load it immediately to catch errors early

    # Import dynamically to avoid circular dependencies
    from .agent_registry import reload_agents
    from .schemas import reload_schemas

    # Invalidate other cached modules
    reload_schemas()
    reload_agents()
    from .tool_registry import reload_tools
    reload_tools()
    from .tool_registry import reload_tools
    reload_tools()
