import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cogni_agents.workflow_engine import run_workflow

@pytest.mark.asyncio
async def test_workflow_step_execution_and_context(mock_test_config):
    """
    Unit tests the workflow engine's logic for step execution, context passing,
    and conditional evaluation by mocking the agent's invoke method.
    """
    # Mock the output of the first agent to control the 'when' condition
    mock_summary_output = MagicMock()
    mock_summary_output.summary = "Mocked summary of the text"

    # Mock the CogniAgent's invoke method to return predefined results
    mock_agent_invoke = AsyncMock(side_effect=[
        mock_summary_output, # Output for summarizer_agent
        "mock sentiment",    # Output for sentiment_agent
    ])

    # Patch the invoke method on the CogniAgent class. This is more reliable
    # for a unit test than patching the agent registry.
    with patch("cogni_agents.cogni_agent.CogniAgent.invoke", new=mock_agent_invoke):
        payload = {"query": "some text"}
        final_context = await run_workflow("test_analysis_workflow", payload)

        # Assertions
        assert mock_agent_invoke.call_count == 2

        # Check first agent call
        # The first argument to invoke is `self`, so we check the second (`args[1]`)
        call1_args = mock_agent_invoke.call_args_list[0].args[1]
        assert call1_args == {"text": "some text"}

        # Check second agent call (verifies conditional step ran)
        call2_args = mock_agent_invoke.call_args_list[1].args[1]
        assert call2_args == {"text": "some text"}

        # Check final context state
        assert final_context["context"]["summary_result"] == mock_summary_output
        assert final_context["context"]["sentiment_result"] == "mock sentiment"
