import pytest
from cogni_agents.cogni_agent import CogniAgent

# Use fixtures from conftest.py to mock dependencies
pytestmark = pytest.mark.usefixtures("mock_global_llm_settings")

def test_cogni_agent_initialization(mock_test_config, mock_openai_chat_model_init):
    """
    Tests that a CogniAgent initializes correctly, merging global and agent-specific settings.
    """
    agent_config = {
        "name": "test_agent",
        "prompt": "Test prompt",
        "output_schema": "str",
        "llm": {"model": "agent-specific-model"}
    }
    agent = CogniAgent(agent_config)

    assert agent.name == "test_agent"

    # Assert that the underlying OpenAIChatModel was initialized with the correctly merged settings.
    # The mock_openai_chat_model_init fixture patches the constructor.
    call_args, call_kwargs = mock_openai_chat_model_init.call_args
    
    # Agent-specific model should override the global default.
    # The underlying library uses 'model_name'.
    assert call_kwargs.get("model_name") == "agent-specific-model"
    # Temperature should be inherited from the mocked global settings
    assert call_kwargs.get("temperature") == 0.1

def test_cogni_agent_build_instructions(mock_test_config, mock_openai_chat_model_init):
    """
    Tests that the agent's instructions are correctly built by rendering prompt components.
    """
    from cogni_agents.config_loader import get_agent_configs
    
    # Get a config that uses a prompt component
    agent_config = next(c for c in get_agent_configs() if c["name"] == "sentiment_agent")
    agent = CogniAgent(agent_config)

    instructions = agent._build_instructions()
    
    # Check that the component was rendered into the instructions
    assert "Analyze sentiment for: {text}." in instructions
    assert "Be polite." in instructions
    assert "{{ prompt_components.politeness }}" not in instructions
