import asyncio
import logging
from typing import Dict

from .config_loader import get_agent_configs
from .cogni_agent import CogniAgent

logger = logging.getLogger(__name__)

_agents: Dict[str, CogniAgent] = {}
_loaded = False
_lock = asyncio.Lock()


async def ensure_agents_loaded():
    """
    Ensures that all agents defined in the configuration are loaded and initialized.
    This function is idempotent and uses an asyncio lock to prevent race conditions
    during concurrent calls.
    """
    global _loaded
    if _loaded:
        logger.debug("Agents already loaded, skipping.")
        return

    async with _lock:
        # Double-check inside the lock in case another coroutine loaded them
        if _loaded:
            logger.debug("Agents already loaded by another coroutine, skipping.")
            return

        logger.info("Loading and initializing CogniAgents...")
        agent_configs = get_agent_configs()
        if not agent_configs:
            logger.warning("No agent configurations found in config.yaml.")
            _loaded = True
            return

        for cfg in agent_configs:
            name = cfg.get("name")
            if not name:
                logger.error(f"Agent configuration missing 'name' field: {cfg}")
                continue
            try:
                _agents[name] = CogniAgent(cfg)
                logger.debug(f"Agent '{name}' initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize agent '{name}': {e}")
                # Depending on desired behavior, you might want to re-raise or skip this agent

        _loaded = True
        logger.info(f"Successfully loaded {len(_agents)} CogniAgents.")


def get_agent(name: str) -> CogniAgent:
    """
    Retrieves an initialized CogniAgent by its name.
    `ensure_agents_loaded()` must be called prior to this function.

    Args:
        name: The name of the agent to retrieve.

    Returns:
        The CogniAgent instance.

    Raises:
        ValueError: If the agent with the given name is not found or not loaded.
    """
    if not _loaded:
        raise ValueError("Agents have not been loaded. Call ensure_agents_loaded() first.")
    agent = _agents.get(name)
    if agent is None:
        raise ValueError(f"Agent '{name}' not found in the registry.")
    return agent

def reload_agents():
    """
    Forces a reload of all agents from the configuration.
    This will re-initialize all CogniAgent instances.
    """
    global _agents, _loaded
    logger.info("Reloading all CogniAgents...")
    _agents = {}
    _loaded = False
    # The next call to ensure_agents_loaded will perform the actual reload
