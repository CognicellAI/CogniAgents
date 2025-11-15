import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict, Type

from pydantic import BaseModel, Field
from pydantic_ai.models.openai import OpenAIChatModel

from cogni_agents.cogni_agent import CogniAgent
from cogni_agents.schemas import SummaryOutput, SentimentOutput, OUTPUT_SCHEMAS


# mock_global_llm_settings, mock_pydantic_ai_agent, mock_openai_chat_model
# are now provided by conftest.py

def test_cogni_agent_initialization_str_output(mock_pydantic_ai_agent_run, mock_openai_chat_model_init):
    """Test CogniAgent initialization with default string output."""
    agent_config = {
        "name": "test_agent",
        "prompt": "Test prompt",
        "llm_model": "agent-specific-model",
        "temperature": 0.5,
    }
    agent = CogniAgent(agent_config)

    assert agent.name == "test_agent"
    assert agent.title == "test_agent"
    assert agent.description is None
    assert agent.prompt == "Test prompt"
    assert agent.llm_model == "agent-specific-model"
    assert agent.temperature == 0.5
    assert agent.output_schema_name is None
    assert agent.output_type == str

    mock_openai_chat_model_init.assert_called_once_with(model="agent-specific-model")
    # PydanticAIAgent is mocked inside mock_pydantic_ai_agent_run, so we need to access it differently
    # The patch target for PydanticAIAgent is in cogni_agents.cogni_agent
    with patch("cogni_agents.cogni_agent.PydanticAIAgent") as MockAgent:
        # Re-initialize agent to capture PydanticAIAgent call
        CogniAgent(agent_config)
        MockAgent.assert_called_once()
        args, kwargs = MockAgent.call_args
        assert kwargs["instructions"] == "Test prompt"
        assert kwargs["output_type"] == str
        assert kwargs["model_settings"]["temperature"] == 0.5


def test_cogni_agent_initialization_pydantic_output(mock_pydantic_ai_agent_run, mock_openai_chat_model_init):
    """Test CogniAgent initialization with a Pydantic output schema."""
    agent_config = {
        "name": "summary_agent",
        "title": "Summary Agent",
        "description": "Summarizes text",
        "prompt": "Summarize this.",
        "llm_model": "summary-model",
        "output_schema": "summary",
        "temperature": 0.2,
    }
    agent = CogniAgent(agent_config)

    assert agent.name == "summary_agent"
    assert agent.output_type == SummaryOutput

    mock_openai_chat_model_init.assert_called_once_with(model="summary-model")
    with patch("cogni_agents.cogni_agent.PydanticAIAgent") as MockAgent:
        CogniAgent(agent_config)
        MockAgent.assert_called_once()
        args, kwargs = MockAgent.call_args
        assert kwargs["instructions"] == "Summarize this."
        assert kwargs["output_type"] == SummaryOutput
        assert kwargs["model_settings"]["temperature"] == 0.2


def test_cogni_agent_initialization_global_llm_settings(mock_pydantic_ai_agent_run, mock_openai_chat_model_init, mock_global_llm_settings):
    """Test CogniAgent uses global LLM settings if not specified in config."""
    agent_config = {
        "name": "global_agent",
        "prompt": "Global prompt",
        "llm_model": None, # Should fall back to global
        "temperature": None, # Should fall back to global
    }
    agent = CogniAgent(agent_config)

    assert agent.llm_model is None
    assert agent.temperature is None

    mock_openai_chat_model_init.assert_called_once_with(model="global-default-model")
    with patch("cogni_agents.cogni_agent.PydanticAIAgent") as MockAgent:
        CogniAgent(agent_config)
        MockAgent.assert_called_once()
        args, kwargs = MockAgent.call_args
        assert kwargs["model_settings"]["temperature"] == 0.1 # From global settings


def test_cogni_agent_initialization_missing_model_name(mock_pydantic_ai_agent_run, mock_openai_chat_model_init, mock_global_llm_settings):
    """Test initialization raises ValueError if no model name is found."""
    mock_global_llm_settings.return_value = {} # No global default
    agent_config = {
        "name": "no_model_agent",
        "prompt": "Prompt",
        "llm_model": None,
    }
    with pytest.raises(ValueError, match="Agent 'no_model_agent' missing LLM model name."):
        CogniAgent(agent_config)


@pytest.mark.asyncio
async def test_cogni_agent_invoke(mock_pydantic_ai_agent_run):
    """Test the invoke method calls the underlying PydanticAIAgent.run."""
    agent_config = {
        "name": "invoke_agent",
        "prompt": "Invoke prompt",
        "llm_model": "invoke-model",
    }
    agent = CogniAgent(agent_config)

    input_text = "This is some input text."
    context = {"key": "value"}
    result = await agent.invoke(input_text, context)

    mock_pydantic_ai_agent_run.assert_called_once_with(input_text)
    assert result == "Mocked summary of: This is some input t..." # Updated based on conftest.py mock


@pytest.mark.asyncio
async def test_cogni_agent_invoke_error_handling(mock_pydantic_ai_agent_run):
    """Test invoke method handles exceptions from PydanticAIAgent.run."""
    agent_config = {
        "name": "error_agent",
        "prompt": "Error prompt",
        "llm_model": "error-model",
    }
    agent = CogniAgent(agent_config)

    mock_pydantic_ai_agent_run.side_effect = Exception("LLM call failed")

    with pytest.raises(Exception, match="LLM call failed"):
        await agent.invoke("input")
