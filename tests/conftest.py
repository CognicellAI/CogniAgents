import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import os

from cogni_agents.config_loader import reload_config, CONFIG_FILE_PATH
from cogni_agents.agent_registry import reload_agents, _agents, _loaded as agents_loaded_flag, _lock as agents_lock
from cogni_agents.workflow_engine import reload_workflows, _workflow_by_name, _workflows_loaded as workflows_loaded_flag, _lock as workflows_lock
from cogni_agents.cogni_agent import CogniAgent
from cogni_agents.schemas import SummaryOutput, SentimentOutput
from pydantic_ai.models.openai import OpenAIChatModel


# Path to the test configuration file
TEST_CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "test_config.yaml")

# --- Fixtures for State Management ---

@pytest.fixture(autouse=True)
def reset_all_modules_state():
    """
    Resets the state of config_loader, agent_registry, and workflow_engine
    before and after each test to ensure isolation.
    """
    # Before test
    # These reloads clear the internal caches of the modules
    reload_config()
    reload_agents()
    reload_workflows()

    # Ensure locks are released if a previous test failed to do so
    if agents_lock.locked():
        agents_lock.release()
    if workflows_lock.locked():
        workflows_lock.release()

    # Patch the module-level _loaded flags to ensure they start as False for each test
    # This is crucial because reload_* functions only reset the flag, but the actual
    # module-level variable might retain state across tests if not explicitly patched.
    with patch('cogni_agents.agent_registry._loaded', False) as mock_agent_loaded_flag:
        with patch('cogni_agents.workflow_engine._workflows_loaded', False) as mock_workflow_loaded_flag:
            # Also patch the internal dictionaries to ensure they are empty
            with patch('cogni_agents.agent_registry._agents', {}) as mock_agents_dict:
                with patch('cogni_agents.workflow_engine._workflow_by_name', {}) as mock_workflows_dict:
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
    Mocks the config.yaml file content for tests by reading from test_config.yaml.
    This fixture is NOT autouse, so tests must explicitly request it.
    It also patches CONFIG_FILE_PATH in config_loader to ensure the mocked file is used.
    """
    with open(TEST_CONFIG_FILE_PATH, 'r') as f:
        test_config_data = f.read()

    # Patch builtins.open to return our test config data
    with patch("builtins.open", mock_open(read_data=test_config_data)) as mock_file_open:
        # Patch CONFIG_FILE_PATH in config_loader to ensure it tries to open the mocked file
        with patch("cogni_agents.config_loader.CONFIG_FILE_PATH", "mocked_config.yaml", create=True):
            # Also patch os.getenv to return our mocked config path if COGNIA_CONFIG_PATH is requested
            with patch("os.getenv", return_value="mocked_config.yaml") as mock_os_getenv:
                yield mock_file_open


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
            "multi_step_workflow": "Summary: {{ results.summary.summary }}\nSentiment: {{ results.sentiment.sentiment }}"
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
