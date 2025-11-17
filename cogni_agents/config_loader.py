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
    Sets the path to the configuration file. This can be used by example scripts
    or tests to dynamically specify which config file to load.
    """
    global _config_file_path, _config
    if _config_file_path != path:
        _config_file_path = path
        _config = None  # Invalidate cache to force reload with new path

def _get_current_config_path() -> str:
    """
    Determines the current configuration file path, prioritizing `_config_file_path`
    then `COGNIA_CONFIG_PATH` environment variable, then the default 'config.yaml'.
    """
    if _config_file_path:
        return _config_file_path
    return os.getenv("COGNIA_CONFIG_PATH", "config.yaml")

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

def get_workflow_configs() -> List[Dict[str, Any]]:
    """
    Retrieves the list of workflow configurations.
    """
    config = _load_config()
    workflows = config.get("workflows", [])
    if not isinstance(workflows, list):
        raise ValueError("Workflows configuration must be a list.")
    return workflows

def get_template(workflow_name: str) -> Optional[str]:
    """
    Retrieves a specific template string by workflow name.
    """
    config = _load_config()
    templates = config.get("templates", {})
    if not isinstance(templates, dict):
        raise ValueError("Templates configuration must be a dictionary.")
    return templates.get(workflow_name)

def get_custom_schema_configs() -> Dict[str, str]:
    """
    Retrieves the custom schema mapping from the configuration.
    Returns a dictionary mapping a schema name to its import path.
    """
    config = _load_config()
    return config.get("custom_schemas", {})

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
    from .workflow_engine import reload_workflows
    from .schemas import reload_schemas

    # Invalidate other cached modules
    reload_schemas()
    reload_agents()
    reload_workflows()
