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
CONFIG_FILE_PATH = os.getenv("COGNIA_CONFIG_PATH", "config.yaml")

_config: Optional[Dict[str, Any]] = None

def _load_config() -> Dict[str, Any]:
    """
    Loads the configuration from the YAML file specified by CONFIG_FILE_PATH.
    Caches the loaded configuration for subsequent calls.
    """
    global _config
    if _config is None:
        try:
            with open(CONFIG_FILE_PATH, 'r') as f:
                _config = yaml.safe_load(f)
            if not isinstance(_config, dict):
                raise ValueError("Config file must contain a dictionary at its root.")
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at {CONFIG_FILE_PATH}")
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
    Useful for development or when config changes externally.
    """
    global _config
    _config = None
    # The CONFIG_FILE_PATH might have changed via environment variable,
    # so re-evaluate it before loading.
    global CONFIG_FILE_PATH
    CONFIG_FILE_PATH = os.getenv("COGNIA_CONFIG_PATH", "config.yaml")
    _load_config() # Load it immediately to catch errors early
