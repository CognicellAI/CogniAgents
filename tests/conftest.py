import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import os

from cogni_agents.config_loader import reload_config
from cogni_agents.agent_registry import reload_agents
from cogni_agents.workflow_engine import reload_workflows
from cogni_agents.schemas import reload_schemas, SummaryOutput, SentimentOutput
from pydantic_ai.models.openai import OpenAIChatModel

# Path to the test configuration file
TEST_CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "test_config.yaml")

@pytest.fixture(autouse=True)
def reset_module_state_after_test():
    """
    Ensures module states are reset after each test runs by calling reload functions.
    This fixture patches config loading during teardown to prevent errors.
    """
    yield
    # In teardown, we want to reset all modules. However, calling reload_config()
    # can fail if the test-specific config path (set by monkeypatch) has been
    # torn down, leading to a FileNotFoundError.
    # We patch _load_config to prevent this file access during teardown,
    # ensuring a clean reset without side effects.
    with patch("cogni_agents.config_loader._load_config", return_value={}):
        reload_config()
        reload_schemas()
        reload_agents()
        reload_workflows()

@pytest.fixture
def mock_test_config(monkeypatch):
    """
    Sets the config path to the test config file and reloads modules
    to ensure the test config is loaded for the test.
    """
    monkeypatch.setenv("COGNIA_CONFIG_PATH", TEST_CONFIG_FILE_PATH)
    # Reload config and schemas to pick up the new env var and custom schemas.
    reload_config()
    reload_schemas()

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
    async def side_effect(self, input_text: str): # `self` here is the PydanticAIAgent instance
        # The `run` method of PydanticAIAgent returns the output object directly.
        if self.output_type == SummaryOutput:
            return SummaryOutput(
                summary=f"Mocked summary of: {input_text[:20]}...",
                positive_aspects=["Mocked positive aspect"],
                negative_aspects=["Mocked negative aspect"],
            )
        elif self.output_type == SentimentOutput:
            return SentimentOutput(sentiment="positive", rationale="Mocked rationale")
        else: # str
            return f"Mocked generic output for: {input_text[:20]}..."

    # Patch the `run` method on the class prototype using autospec=True
    # This ensures that the mock has the correct signature and `self` is passed.
    with patch("pydantic_ai.Agent.run", side_effect=side_effect, autospec=True) as mock_run:
        yield mock_run
