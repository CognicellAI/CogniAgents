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

        # Check first agent call by inspecting positional arguments
        # args[0] is the `self` instance of CogniAgent, args[1] is the input_data dict
        call1_args = mock_agent_invoke.call_args_list[0].args
        assert call1_args[1] == {"text": "some text"}

        # Check second agent call (verifies conditional step ran)
        call2_args = mock_agent_invoke.call_args_list[1].args
        assert call2_args[1] == {"text": "some text"}

        # Check final context state
        assert final_context["context"]["summary_result"] == mock_summary_output
        assert final_context["context"]["sentiment_result"] == "mock sentiment"
