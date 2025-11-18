import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cogni_agents.workflow_engine import run_workflow
from cogni_agents.cogni_agent import CogniAgent

@pytest.mark.asyncio
async def test_workflow_step_execution_and_context(mock_test_config):
    """
    Unit tests the workflow engine's logic for step execution, context passing,
    and conditional evaluation by mocking the agent registry.
    """
    # Mock the output of the first agent to control the 'when' condition
    mock_summary_output = MagicMock()
    mock_summary_output.summary = "Mocked summary of the text"

    # Create a mock agent instance that will be returned by get_agent
    mock_agent = MagicMock(spec=CogniAgent)
    mock_agent.invoke = AsyncMock(side_effect=[
        mock_summary_output, # Output for summarizer_agent
        "mock sentiment",    # Output for sentiment_agent
    ])

    # Patch get_agent within the workflow_engine module to return our mock agent
    with patch("cogni_agents.workflow_engine.get_agent", return_value=mock_agent):
        payload = {"query": "some text"}
        final_context = await run_workflow("test_analysis_workflow", payload)

        # Assertions
        assert mock_agent.invoke.call_count == 2

        # Check first agent call. The mock method is called with one positional arg.
        call1_args = mock_agent.invoke.call_args_list[0].args
        assert call1_args[0] == {"text": "some text"}

        # Check second agent call (verifies conditional step ran)
        call2_args = mock_agent.invoke.call_args_list[1].args
        assert call2_args[0] == {"text": "some text"}

        # Check final context state
        assert final_context["context"]["summary_result"] == mock_summary_output
        assert final_context["context"]["sentiment_result"] == "mock sentiment"
