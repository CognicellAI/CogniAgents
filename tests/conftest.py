import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import os

from cogni_agents.config_loader import reload_config
from cogni_agents.agent_registry import reload_agents
from cogni_agents.workflow_engine import reload_workflows
from cogni_agents.schemas import SummaryOutput, SentimentOutput
from pydantic_ai.models.openai import OpenAIChatModel

# Path to the test configuration file
TEST_CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "test_config.yaml")

@pytest.fixture(autouse=True)
def reset_module_state_after_test():
    """Ensures module states are reset after each test runs by calling reload functions."""
    yield
    # These functions reset the internal state of each module
    reload_config()
    reload_agents()
    reload_workflows()

@pytest.fixture
def mock_test_config(monkeypatch):
    """
    Sets the config path to the test config file and reloads modules
    to ensure the test config is loaded for the test.
    """
    monkeypatch.setenv("COGNIA_CONFIG_PATH", TEST_CONFIG_FILE_PATH)
    # Reload config to pick up the new env var.
    reload_config()

@pytest.fixture
def mock_global_llm_settings():
    """Mocks the get_global_llm_settings function from config_loader."""
    with patch("cogni_agents.cogni_agent.get_global_llm_settings") as mock_get:
        mock_get.return_value = {"model": "global-default-model", "temperature": 0.1}
        yield mock_get

@pytest.fixture
def mock_openai_chat_model_init():
    """Mocks the OpenAIChatModel constructor to prevent actual API calls."""
    with patch("cogni_agents.cogni_agent.OpenAIChatModel") as mock_chat_model:
        mock_chat_model.return_value = MagicMock(spec=OpenAIChatModel)
        yield mock_chat_model

@pytest.fixture
def mock_pydantic_ai_agent_run():
    """
    Mocks the `run` method of PydanticAIAgent to control LLM responses
    based on the `output_type` of the agent instance.
    """
    # This is the mock we will assert against.
    mock_run = AsyncMock()

    async def side_effect(self, input_text: str): # `self` here is the PydanticAIAgent instance
        mock_result = MagicMock()
        # We can access the output_type from the instance
        if self.output_type == SummaryOutput:
            mock_result.output = SummaryOutput(summary=f"Mocked summary of: {input_text[:20]}...")
        elif self.output_type == SentimentOutput:
            mock_result.output = SentimentOutput(sentiment="positive", rationale="Mocked rationale")
        else: # str
            mock_result.output = f"Mocked generic output for: {input_text[:20]}..."
        return mock_result

    mock_run.side_effect = side_effect

    # Patch the `run` method on the class prototype
    with patch("pydantic_ai.Agent.run", new=mock_run):
        yield mock_run
