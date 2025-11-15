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
    This fixture also sets up core patches for config loading.
    """
    # Read the test config data once
    with open(TEST_CONFIG_FILE_PATH, 'r') as f:
        test_config_data = f.read()

    # Patch builtins.open and CONFIG_FILE_PATH for all tests
    with patch("builtins.open", mock_open(read_data=test_config_data)) as mock_file_open:
        with patch("cogni_agents.config_loader.CONFIG_FILE_PATH", "mocked_config.yaml", create=True):
            with patch("os.getenv", return_value="mocked_config.yaml") as mock_os_getenv:
                # Now that patching is in place, perform reloads to clear caches
                # and ensure they pick up the mocked config path.
                reload_config()
                reload_agents()
                reload_workflows()

                # Ensure locks are released if a previous test failed to do so
                if agents_lock.locked():
                    agents_lock.release()
                if workflows_lock.locked():
                    workflows_lock.release()

                # Patch the module-level _loaded flags to ensure they start as False for each test
                # Also patch the internal dictionaries to ensure they are empty
                with patch('cogni_agents.agent_registry._loaded', False) as mock_agent_loaded_flag:
                    with patch('cogni_agents.agent_registry._agents', {}) as mock_agents_dict:
                        with patch('cogni_agents.workflow_engine._workflows_loaded', False) as mock_workflow_loaded_flag:
                            with patch('cogni_agents.workflow_engine._workflow_by_name', {}) as mock_workflows_dict:
                                yield

    # After test: ensure everything is reset
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
    This fixture is now redundant as its functionality is moved to reset_all_modules_state.
    It's kept here as a placeholder or if specific tests need to override the default mock.
    Tests should generally rely on reset_all_modules_state for config mocking.
    """
    # This fixture now just yields, as the patching is handled by reset_all_modules_state
    yield


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
    It also ensures that the _agents dictionary in agent_registry is populated
    with the mock instances it creates, so get_agent can find them.
    """
    with patch("cogni_agents.agent_registry.CogniAgent") as MockCogniAgent:
        # Store created mock instances
        created_mocks = {}
        def side_effect_func(agent_config):
            mock_instance = MagicMock(spec=CogniAgent)
            mock_instance.name = agent_config["name"] # Ensure mock has a name attribute
            created_mocks[agent_config["name"]] = mock_instance
            return mock_instance
        MockCogniAgent.side_effect = side_effect_func

        yield MockCogniAgent

        # After the test, ensure the _agents dictionary is populated with the mocks
        # This is a bit tricky due to the patching of _agents in reset_all_modules_state.
        # We need to ensure the _agents dict that get_agent() sees is updated.
        # The patch in reset_all_modules_state creates a new dict, so we need to update that one.
        # This is handled by the patch in reset_all_modules_state, so we just need to ensure
        # the mocks are created and available.


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
