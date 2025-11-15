import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from cogni_agents.workflow_engine import (
    load_workflows,
    run_workflow,
    _resolve_path,
    render_workflow_output,
    reload_workflows,
    _workflow_by_name,
    _workflows_loaded,
    _lock
)
from cogni_agents.cogni_agent import CogniAgent
from cogni_agents.schemas import SummaryOutput, SentimentOutput

@pytest.fixture
def mock_get_workflow_configs():
    """Mocks get_workflow_configs from config_loader for workflow_engine tests."""
    with patch("cogni_agents.workflow_engine.get_workflow_configs") as mock_gwc:
        mock_gwc.return_value = [
            {
                "name": "test_workflow_1",
                "description": "Workflow 1",
                "steps": [
                    {"agent": "agent1", "input_from": "payload.text", "save_as": "step1_result"}
                ]
            },
            {
                "name": "test_workflow_2",
                "description": "Workflow 2",
                "steps": [
                    {"agent": "agent2", "input_from": "results.step1_result.summary", "save_as": "step2_result"}
                ]
            }
        ]
        yield mock_gwc

@pytest.fixture
def mock_get_template():
    """Mocks get_template from config_loader for workflow_engine tests."""
    with patch("cogni_agents.workflow_engine.get_template") as mock_gt:
        mock_gt.side_effect = {
            "test_workflow_1": "Summary: {{ results.step1_result.summary }}",
            "test_workflow_with_payload_template": "Original: {{ payload.original_text }}. Output: {{ results.generic_output }}",
            "test_workflow_no_template": None
        }.get
        yield mock_gt

@pytest.fixture
def mock_agent_registry_for_workflow_engine():
    """Mocks ensure_agents_loaded and get_agent from agent_registry for workflow_engine tests."""
    with patch("cogni_agents.workflow_engine.ensure_agents_loaded", new_callable=AsyncMock) as mock_eal, \
         patch("cogni_agents.workflow_engine.get_agent") as mock_ga:

        mock_agent1 = MagicMock(spec=CogniAgent)
        mock_agent1.invoke = AsyncMock(return_value=SummaryOutput(summary="mocked summary 1"))

        mock_agent2 = MagicMock(spec=CogniAgent)
        mock_agent2.invoke = AsyncMock(return_value=SentimentOutput(sentiment="positive", rationale="good"))

        mock_ga.side_effect = lambda name: {
            "agent1": mock_agent1,
            "agent2": mock_agent2,
        }.get(name)
        yield mock_eal, mock_ga


@pytest.mark.asyncio
async def test_load_workflows_first_time(mock_get_workflow_configs):
    """Test that workflows are loaded and indexed correctly the first time."""
    await load_workflows()

    assert _workflows_loaded
    assert len(_workflow_by_name) == 2
    mock_get_workflow_configs.assert_called_once()
    assert "test_workflow_1" in _workflow_by_name
    assert "test_workflow_2" in _workflow_by_name
    assert _workflow_by_name["test_workflow_1"]["description"] == "Workflow 1"


@pytest.mark.asyncio
async def test_load_workflows_idempotent(mock_get_workflow_configs):
    """Test that load_workflows is idempotent and doesn't reload."""
    await load_workflows() # First load
    mock_get_workflow_configs.reset_mock()

    await load_workflows() # Second call

    mock_get_workflow_configs.assert_not_called()
    assert _workflows_loaded
    assert len(_workflow_by_name) == 2


@pytest.mark.asyncio
async def test_load_workflows_no_configs(mock_get_workflow_configs):
    """Test behavior when no workflow configurations are found."""
    mock_get_workflow_configs.return_value = []
    await load_workflows()
    assert _workflows_loaded
    assert not _workflow_by_name
    mock_get_workflow_configs.assert_called_once()


@pytest.mark.asyncio
async def test_load_workflows_config_missing_name(mock_get_workflow_configs, caplog):
    """Test that workflows with missing names are skipped and logged."""
    mock_get_workflow_configs.return_value = [
        {"name": "valid_workflow", "steps": []},
        {"description": "Invalid workflow", "steps": []}, # Missing name
    ]
    with caplog.at_level("ERROR"):
        await load_workflows()

    assert _workflows_loaded
    assert len(_workflow_by_name) == 1
    assert "valid_workflow" in _workflow_by_name
    assert "Workflow configuration missing 'name' field" in caplog.text


@pytest.mark.asyncio
async def test_run_workflow_success(mock_get_workflow_configs, mock_agent_registry_for_workflow_engine):
    """Test successful execution of a single-step workflow."""
    mock_eal, mock_ga = mock_agent_registry_for_workflow_engine
    payload = {"text": "document content"}
    context = await run_workflow("test_workflow_1", payload)

    mock_eal.assert_called_once()
    mock_ga.assert_called_once_with("agent1")
    mock_ga.return_value.invoke.assert_called_once_with("document content", context={"payload": payload, "results": {}})

    assert "payload" in context
    assert "results" in context
    assert context["payload"] == payload
    assert isinstance(context["results"]["step1_result"], SummaryOutput)
    assert context["results"]["step1_result"].summary == "mocked summary 1"


@pytest.mark.asyncio
async def test_run_workflow_multi_step_success(mock_get_workflow_configs, mock_agent_registry_for_workflow_engine):
    """Test successful execution of a multi-step workflow."""
    mock_get_workflow_configs.return_value = [
        {
            "name": "multi_step_workflow",
            "steps": [
                {"agent": "agent1", "input_from": "payload.content", "save_as": "summary"},
                {"agent": "agent2", "input_from": "results.summary.summary", "save_as": "sentiment"},
            ]
        }
    ]
    mock_eal, mock_ga = mock_agent_registry_for_workflow_engine
    payload = {"content": "This is a great document."}
    context = await run_workflow("multi_step_workflow", payload)

    assert mock_ga.call_count == 2
    mock_ga.assert_any_call("agent1")
    mock_ga.assert_any_call("agent2")

    mock_ga.side_effect("agent1").invoke.assert_called_once_with("This is a great document.", context=patch.ANY)
    mock_ga.side_effect("agent2").invoke.assert_called_once_with("mocked summary 1", context=patch.ANY)

    assert isinstance(context["results"]["summary"], SummaryOutput)
    assert context["results"]["summary"].summary == "mocked summary 1"
    assert isinstance(context["results"]["sentiment"], SentimentOutput)
    assert context["results"]["sentiment"].sentiment == "positive"


@pytest.mark.asyncio
async def test_run_workflow_not_found(mock_get_workflow_configs, mock_agent_registry_for_workflow_engine):
    """Test run_workflow raises ValueError if workflow is not found."""
    with pytest.raises(ValueError, match="Workflow 'non_existent_workflow' not found."):
        await run_workflow("non_existent_workflow", {"text": "input"})


@pytest.mark.asyncio
async def test_run_workflow_agent_invocation_error(mock_get_workflow_configs, mock_agent_registry_for_workflow_engine):
    """Test run_workflow handles errors during agent invocation."""
    mock_eal, mock_ga = mock_agent_registry_for_workflow_engine
    mock_ga.return_value.invoke.side_effect = Exception("Agent failed")

    with pytest.raises(Exception, match="Agent failed"):
        await run_workflow("test_workflow_1", {"text": "input"})


def test_resolve_path_success():
    """Test _resolve_path with a valid dotted path."""
    ctx = {"payload": {"content": "hello"}, "results": {"summary": {"text": "hi"}}}
    assert _resolve_path(ctx, "payload.content") == "hello"
    assert _resolve_path(ctx, "results.summary.text") == "hi"


def test_resolve_path_key_error():
    """Test _resolve_path raises KeyError for non-existent path."""
    ctx = {"payload": {"content": "hello"}}
    with pytest.raises(KeyError, match="Missing key 'results'"):
        _resolve_path(ctx, "results.summary")


def test_resolve_path_type_error():
    """Test _resolve_path raises TypeError if intermediate part of the path is not a dict."""
    ctx = {"payload": "not_a_dict"}
    with pytest.raises(TypeError, match="'payload' is not a dictionary or Pydantic model."):
        _resolve_path(ctx, "payload.content")


def test_render_workflow_output_with_template(mock_get_template):
    """Test rendering output when a template is available."""
    context = {
        "payload": {"content": "original text"},
        "results": {"step1_result": SummaryOutput(summary="short summary")}
    }
    output = render_workflow_output("test_workflow_1", context)
    assert output == "Summary: short summary"
    mock_get_template.assert_called_once_with("test_workflow_1")


def test_render_workflow_output_with_payload_in_template(mock_get_template):
    """Test rendering output when a template uses payload data."""
    context = {
        "payload": {"original_text": "original text content"},
        "results": {"generic_output": "some generic output"}
    }
    output = render_workflow_output("test_workflow_with_payload_template", context)
    assert output == "Original: original text content. Output: some generic output"
    mock_get_template.assert_called_once_with("test_workflow_with_payload_template")


def test_render_workflow_output_no_template(mock_get_template):
    """Test rendering output when no template is available."""
    context = {
        "payload": {"content": "original text"},
        "results": {"step2_result": SentimentOutput(sentiment="positive", rationale="good")}
    }
    output = render_workflow_output("test_workflow_no_template", context)
    # Default behavior is to return string representation of results
    assert "sentiment='positive' rationale='good'" in output
    mock_get_template.assert_called_once_with("test_workflow_no_template")


def test_render_workflow_output_template_error(mock_get_template, caplog):
    """Test rendering output handles template errors gracefully."""
    mock_get_template.return_value = "Invalid template: {{ results.non_existent_var }}"
    context = {
        "payload": {"content": "original text"},
        "results": {"step1_result": SummaryOutput(summary="short summary")}
    }
    with caplog.at_level("ERROR"):
        output = render_workflow_output("test_workflow_1", context)
        assert "Error rendering template" in caplog.text
        # Should fall back to string representation of results
        assert "summary='short summary'" in output


@pytest.mark.asyncio
async def test_reload_workflows(mock_get_workflow_configs):
    """Test that reload_workflows resets the state for a fresh load."""
    await load_workflows()
    assert _workflows_loaded
    assert len(_workflow_by_name) > 0

    reload_workflows()

    assert not _workflows_loaded
    assert not _workflow_by_name
    # Calling load_workflows again should trigger a full reload
    mock_get_workflow_configs.reset_mock() # Reset mock to count calls for reload
    mock_get_workflow_configs.return_value = [{"name": "reloaded_wf", "steps": []}]
    await load_workflows()
    mock_get_workflow_configs.assert_called_once()
    assert _workflows_loaded
    assert "reloaded_wf" in _workflow_by_name
