import pytest
from unittest.mock import patch
from cogni_agents.cogni_agent import CogniAgent

# No longer using pytestmark to apply fixtures globally

def test_cogni_agent_initialization(mock_test_config, mock_openai_chat_model_init):
    """
    Tests that a CogniAgent initializes correctly, merging global and agent-specific settings.
    """
    agent_config = {
        "name": "test_agent",
        "prompt": "Test prompt",
        "output_schema": "str",
        "llm": {"model": "agent-specific-model", "temperature": 0.9}
    }

    # Mock get_global_llm_settings just for this test to ensure isolation
    with patch("cogni_agents.cogni_agent.get_global_llm_settings") as mock_get_globals:
        mock_get_globals.return_value = {"model": "global-default-model", "temperature": 0.1}

        # Patch PydanticAIAgent to inspect the arguments it's called with
        with patch("cogni_agents.cogni_agent.PydanticAIAgent") as mock_pydantic_agent:
            agent = CogniAgent(agent_config)

            assert agent.name == "test_agent"

            # Assert that OpenAIChatModel was initialized with the correct, overridden model name
            mock_openai_chat_model_init.assert_called_with(model_name="agent-specific-model")

            # Assert that PydanticAIAgent was initialized with the correct remaining settings
            call_args, call_kwargs = mock_pydantic_agent.call_args
            
            # The agent-specific temperature (0.9) should override the global one (0.1)
            assert call_kwargs.get("model_settings") == {"temperature": 0.9}

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
