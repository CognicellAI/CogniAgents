import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cogni_agents.workflow_engine import run_workflow

@pytest.mark.asyncio
async def test_workflow_step_execution_and_context(mock_test_config):
    """
    Unit tests the workflow engine's logic for step execution, context passing,
    and conditional evaluation by mocking the agent calls.
    """
    # Mock the output of the first agent to control the 'when' condition
    mock_summary_output = MagicMock()
    mock_summary_output.summary = "Mocked summary of the text"

    # Mock the CogniAgent's invoke method
    mock_agent_invoke = AsyncMock(side_effect=[
        mock_summary_output, # Output for summarizer_agent
        "mock sentiment",    # Output for sentiment_agent
    ])

    # Mock the agent object itself
    mock_agent = MagicMock()
    mock_agent.invoke = mock_agent_invoke

    # Patch get_agent to always return our fully mocked agent
    with patch("cogni_agents.agent_registry.get_agent", return_value=mock_agent):
        payload = {"query": "some text"}
        final_context = await run_workflow("test_analysis_workflow", payload)

        # Assertions
        assert mock_agent_invoke.call_count == 2

        # Check first agent call
        call1_args = mock_agent_invoke.call_args_list[0].args[0]
        assert call1_args == {"text": "some text"}

        # Check second agent call (verifies conditional step ran)
        call2_args = mock_agent_invoke.call_args_list[1].args[0]
        assert call2_args == {"text": "some text"}

        # Check final context state
        assert final_context["context"]["summary_result"] == mock_summary_output
        assert final_context["context"]["sentiment_result"] == "mock sentiment"
