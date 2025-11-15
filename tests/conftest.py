import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from cogni_agents.config_loader import reload_config, CONFIG_FILE_PATH
from cogni_agents.agent_registry import reload_agents, _agents, _loaded as agents_loaded_flag, _lock as agents_lock
from cogni_agents.workflow_engine import reload_workflows, _workflow_by_name, _workflows_loaded as workflows_loaded_flag, _lock as workflows_lock
from cogni_agents.cogni_agent import CogniAgent
from cogni_agents.schemas import SummaryOutput, SentimentOutput
from pydantic_ai.models.openai import OpenAIChatModel


# --- Global Test Configuration ---

# Sample config content for testing various modules
SAMPLE_CONFIG_CONTENT = """
global_llm_settings:
  model: "test-model"
  temperature: 0.5

agents:
  - name: "test_agent_1"
    prompt: "Test prompt 1"
    llm_model: "model-1"
    output_schema: "summary"
  - name: "test_agent_2"
    prompt: "Test prompt 2"
    llm_model: "model-2"
    output_schema: "sentiment"
  - name: "agent_no_schema"
    prompt: "No schema"
    llm_model: "model-3"

workflows:
  - name: "test_workflow_1"
    steps:
      - agent: "test_agent_1"
        input_from: "payload.text"
        save_as: "step1_result"
  - name: "test_workflow_2"
    steps:
      - agent: "test_agent_2"
        input_from: "results.step1_result.summary"
        save_as: "step2_result"
  - name: "test_workflow_with_payload_template"
    steps:
      - agent: "agent_no_schema"
        input_from: "payload.original_text"
        save_as: "generic_output"
  - name: "multi_step_workflow" # Added for workflow_engine test
    steps:
      - agent: "test_agent_1"
        input_from: "payload.content"
        save_as: "summary"
      - agent: "test_agent_2"
        input_from: "results.summary.summary"
        save_as: "sentiment"

templates:
  test_workflow_1: "Summary: {{ results.step1_result.summary }}"
  test_workflow_with_payload_template: "Original: {{ payload.original_text }}. Output: {{ results.generic_output }}"
  test_workflow_no_template: null # Explicitly no template
  multi_step_workflow: |
    ## Multi-Step Report
    Summary: {{ results.summary.summary }}
    Sentiment: {{ results.sentiment.sentiment }} ({{ results.sentiment.rationale }})

defaults:
  max_tokens: 1024
  language: "en"
"""

# --- Fixtures for State Management ---

@pytest.fixture(autouse=True)
def reset_all_modules_state():
    """
    Resets the state of config_loader, agent_registry, and workflow_engine
    before and after each test to ensure isolation.
    """
    # Before test
    reload_config()
    reload_agents()
    reload_workflows()

    # Ensure locks are released if a previous test failed to do so
    if agents_lock.locked():
        agents_lock.release()
    if workflows_lock.locked():
        workflows_lock.release()

    # Manually reset the _loaded flags for agent_registry and workflow_engine
    # as they are internal to the modules and not directly exposed by reload_* functions
    with patch('cogni_agents.agent_registry._loaded', False, create=True):
        with patch('cogni_agents.workflow_engine._workflows_loaded', False, create=True):
            yield

    # After test
    reload_config()
    reload_agents()
    reload_workflows()
    if agents_lock.locked():
        agents_lock.release()
    if workflows_lock.locked():
        workflows_lock.release()


@pytest.fixture
def mock_config_content():
    """
    Mocks the config.yaml file content for tests.
    This fixture is NOT autouse, so tests must explicitly request it.
    """
    with patch("builtins.open", mock_open(read_data=SAMPLE_CONFIG_CONTENT)) as mock_file:
        yield mock_file


# --- Fixtures for Mocking External Dependencies ---

@pytest.fixture
def mock_global_llm_settings():
    """
    Mocks the get_global_llm_settings function from config_loader.
    """
    with patch("cogni_agents.cogni_agent.get_global_llm_settings") as mock_get_global_llm_settings:
        mock_get_global_llm_settings.return_value = {
            "model": "global-default-model",
            "temperature": 0.1
        }
        yield mock_get_global_llm_settings


@pytest.fixture
def mock_openai_chat_model_init():
    """
    Mocks the OpenAIChatModel constructor to prevent actual API calls.
    """
    with patch("cogni_agents.cogni_agent.OpenAIChatModel") as mock_chat_model:
        mock_chat_model.return_value = MagicMock(spec=OpenAIChatModel)
        yield mock_chat_model


@pytest.fixture
def mock_pydantic_ai_agent_run():
    """
    Mocks the `run` method of PydanticAIAgent to control LLM responses.
    """
    with patch("pydantic_ai.Agent.run", new_callable=AsyncMock) as mock_run:
        # Configure side_effect to return different outputs based on agent's purpose
        def side_effect_func(input_text: str):
            if "Summarize" in input_text or "summary" in input_text.lower():
                mock_result = MagicMock()
                mock_result.output = SummaryOutput(summary=f"Mocked summary of: {input_text[:20]}...")
                return mock_result
            elif "sentiment" in input_text.lower():
                mock_result = MagicMock()
                mock_result.output = SentimentOutput(sentiment="positive", rationale="Mocked rationale")
                return mock_result
            else:
                mock_result = MagicMock()
                mock_result.output = f"Mocked generic output for: {input_text[:20]}..."
                return mock_result

        mock_run.side_effect = side_effect_func
        yield mock_run


@pytest.fixture
def mock_cogni_agent_constructor():
    """
    Mocks the CogniAgent constructor for agent_registry tests.
    """
    with patch("cogni_agents.agent_registry.CogniAgent") as MockCogniAgent:
        # Configure the mock constructor to return a mock instance
        MockCogniAgent.return_value = MagicMock(spec=CogniAgent)
        yield MockCogniAgent


@pytest.fixture
def mock_get_agent_configs():
    """
    Mocks get_agent_configs from config_loader for agent_registry tests.
    """
    with patch("cogni_agents.agent_registry.get_agent_configs") as mock_gac:
        mock_gac.return_value = [
            {"name": "agent1", "prompt": "Prompt 1", "llm_model": "model1"},
            {"name": "agent2", "prompt": "Prompt 2", "llm_model": "model2"},
        ]
        yield mock_gac


@pytest.fixture
def mock_get_workflow_configs():
    """
    Mocks get_workflow_configs from config_loader for workflow_engine tests.
    """
    with patch("cogni_agents.workflow_engine.get_workflow_configs") as mock_gwc:
        mock_gwc.return_value = [
            {
                "name": "test_workflow_1",
                "description": "Workflow 1",
                "steps": [
                    {"agent": "test_agent_1", "input_from": "payload.text", "save_as": "step1_result"}
                ]
            },
            {
                "name": "test_workflow_2",
                "description": "Workflow 2",
                "steps": [
                    {"agent": "test_agent_2", "input_from": "results.step1_result.summary", "save_as": "step2_result"}
                ]
            },
            {
                "name": "multi_step_workflow",
                "description": "Multi-step workflow for integration.",
                "steps": [
                    {"agent": "test_agent_1", "input_from": "payload.content", "save_as": "summary_result"},
                    {"agent": "test_agent_2", "input_from": "results.summary_result.summary", "save_as": "sentiment_result"},
                ]
            }
        ]
        yield mock_gwc


@pytest.fixture
def mock_get_template():
    """
    Mocks get_template from config_loader for workflow_engine tests.
    """
    with patch("cogni_agents.workflow_engine.get_template") as mock_gt:
        mock_gt.side_effect = {
            "test_workflow_1": "Summary: {{ results.step1_result.summary }}",
            "test_workflow_with_payload_template": "Original: {{ payload.original_text }}. Output: {{ results.generic_output }}",
            "test_workflow_no_template": None,
            "multi_step_workflow": "Summary: {{ results.summary_result.summary }}\nSentiment: {{ results.sentiment_result.sentiment }}"
        }.get
        yield mock_gt


@pytest.fixture
def mock_agent_registry_for_workflow_engine():
    """
    Mocks ensure_agents_loaded and get_agent from agent_registry for workflow_engine tests.
    """
    with patch("cogni_agents.workflow_engine.ensure_agents_loaded", new_callable=AsyncMock) as mock_eal, \
         patch("cogni_agents.workflow_engine.get_agent") as mock_ga:

        # Mock CogniAgent instances
        mock_agent1 = MagicMock(spec=CogniAgent)
        mock_agent1.invoke = AsyncMock(return_value=SummaryOutput(summary="mocked summary 1"))

        mock_agent2 = MagicMock(spec=CogniAgent)
        mock_agent2.invoke = AsyncMock(return_value=SentimentOutput(sentiment="positive", rationale="good"))

        mock_agent_no_schema = MagicMock(spec=CogniAgent)
        mock_agent_no_schema.invoke = AsyncMock(return_value="mocked generic output")

        mock_ga.side_effect = lambda name: {
            "test_agent_1": mock_agent1, # Use names from SAMPLE_CONFIG_CONTENT
            "test_agent_2": mock_agent2, # Use names from SAMPLE_CONFIG_CONTENT
            "agent_no_schema": mock_agent_no_schema,
            "agent1": mock_agent1, # For agent_registry tests that use agent1/agent2
            "agent2": mock_agent2, # For agent_registry tests that use agent1/agent2
        }.get(name)
        yield mock_eal, mock_ga
