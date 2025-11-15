import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from cogni_agents.agent_registry import (
    ensure_agents_loaded,
    get_agent,
    reload_agents,
    _agents,
    _loaded,
    _lock
)
from cogni_agents.cogni_agent import CogniAgent

@pytest.fixture
def mock_get_agent_configs():
    """Mocks get_agent_configs from config_loader for agent_registry tests."""
    with patch("cogni_agents.agent_registry.get_agent_configs") as mock_gac:
        mock_gac.return_value = [
            {"name": "agent1", "prompt": "Prompt 1", "llm_model": "model1"},
            {"name": "agent2", "prompt": "Prompt 2", "llm_model": "model2"},
        ]
        yield mock_gac

@pytest.fixture
def mock_cogni_agent_constructor():
    """Mocks the CogniAgent constructor for agent_registry tests."""
    with patch("cogni_agents.agent_registry.CogniAgent") as MockCogniAgent:
        # Configure the mock constructor to return a mock instance with a name
        def side_effect(config):
            instance = MagicMock(spec=CogniAgent)
            instance.name = config["name"]
            return instance
        MockCogniAgent.side_effect = side_effect
        yield MockCogniAgent


@pytest.mark.asyncio
async def test_ensure_agents_loaded_first_time(mock_get_agent_configs, mock_cogni_agent_constructor):
    """Test that agents are loaded and initialized correctly the first time."""
    await ensure_agents_loaded()

    assert _loaded
    assert len(_agents) == 2
    mock_get_agent_configs.assert_called_once()
    assert mock_cogni_agent_constructor.call_count == 2
    mock_cogni_agent_constructor.assert_any_call({"name": "agent1", "prompt": "Prompt 1", "llm_model": "model1"})
    mock_cogni_agent_constructor.assert_any_call({"name": "agent2", "prompt": "Prompt 2", "llm_model": "model2"})
    assert isinstance(_agents["agent1"], MagicMock)
    assert isinstance(_agents["agent2"], MagicMock)


@pytest.mark.asyncio
async def test_ensure_agents_loaded_idempotent(mock_get_agent_configs, mock_cogni_agent_constructor):
    """Test that ensure_agents_loaded is idempotent and doesn't reload."""
    await ensure_agents_loaded() # First load
    mock_get_agent_configs.reset_mock()
    mock_cogni_agent_constructor.reset_mock()

    await ensure_agents_loaded() # Second call

    mock_get_agent_configs.assert_not_called()
    mock_cogni_agent_constructor.assert_not_called()
    assert _loaded
    assert len(_agents) == 2


@pytest.mark.asyncio
async def test_ensure_agents_loaded_no_configs(mock_get_agent_configs, mock_cogni_agent_constructor):
    """Test behavior when no agent configurations are found."""
    mock_get_agent_configs.return_value = []
    await ensure_agents_loaded()
    assert _loaded
    assert not _agents
    mock_get_agent_configs.assert_called_once()
    mock_cogni_agent_constructor.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_agents_loaded_config_missing_name(mock_get_agent_configs, mock_cogni_agent_constructor, caplog):
    """Test that agents with missing names are skipped and logged."""
    mock_get_agent_configs.return_value = [
        {"name": "valid_agent", "prompt": "P", "llm_model": "M"},
        {"prompt": "Invalid", "llm_model": "M"}, # Missing name
    ]
    with caplog.at_level("ERROR"):
        await ensure_agents_loaded()

    assert _loaded
    assert len(_agents) == 1
    assert "valid_agent" in _agents
    assert "Agent configuration missing 'name' field" in caplog.text
    mock_cogni_agent_constructor.assert_called_once_with({"name": "valid_agent", "prompt": "P", "llm_model": "M"})


@pytest.mark.asyncio
async def test_ensure_agents_loaded_cogniagent_init_failure(mock_get_agent_configs, mock_cogni_agent_constructor, caplog):
    """Test that agent initialization failures are caught and logged."""
    mock_cogni_agent_constructor.side_effect = [
        MagicMock(spec=CogniAgent), # agent1 succeeds
        Exception("Failed to init agent2") # agent2 fails
    ]
    with caplog.at_level("ERROR"):
        await ensure_agents_loaded()

    assert _loaded
    assert len(_agents) == 1
    assert "agent1" in _agents
    assert "agent2" not in _agents
    assert "Failed to initialize agent 'agent2': Failed to init agent2" in caplog.text


@pytest.mark.asyncio
async def test_get_agent_success(mock_get_agent_configs, mock_cogni_agent_constructor):
    """Test retrieving an agent by name after loading."""
    await ensure_agents_loaded()
    agent = get_agent("agent1")
    assert agent is _agents["agent1"]
    assert isinstance(agent, MagicMock)


@pytest.mark.asyncio
async def test_get_agent_not_loaded():
    """Test get_agent raises ValueError if agents are not loaded."""
    with pytest.raises(ValueError, match="Agents have not been loaded."):
        get_agent("agent1")


@pytest.mark.asyncio
async def test_get_agent_not_found(mock_get_agent_configs, mock_cogni_agent_constructor):
    """Test get_agent raises ValueError if agent name is not in registry."""
    await ensure_agents_loaded()
    with pytest.raises(ValueError, match="Agent 'non_existent_agent' not found in the registry."):
        get_agent("non_existent_agent")


@pytest.mark.asyncio
async def test_reload_agents(mock_get_agent_configs, mock_cogni_agent_constructor):
    """Test that reload_agents resets the state for a fresh load."""
    await ensure_agents_loaded()
    assert _loaded
    assert len(_agents) > 0

    reload_agents()

    assert not _loaded
    assert not _agents
    # Calling ensure_agents_loaded again should trigger a full reload
    mock_get_agent_configs.reset_mock()
    mock_cogni_agent_constructor.reset_mock()

    await ensure_agents_loaded()
    mock_get_agent_configs.assert_called_once()
    assert mock_cogni_agent_constructor.call_count == 2
    assert _loaded
    assert len(_agents) == 2
