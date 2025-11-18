import pytest
from cogni_agents.workflow_engine import run_workflow, render_workflow_output
from cogni_agents.schemas import SummaryOutput, SentimentOutput

# These fixtures are defined in conftest.py and are essential for this test
pytestmark = pytest.mark.usefixtures("mock_test_config", "mock_pydantic_ai_agent_run")

@pytest.mark.asyncio
async def test_e2e_workflow_with_mocked_llm():
    """
    Tests the full workflow from config loading to final output rendering.
    The `mock_pydantic_ai_agent_run` fixture intercepts calls to the LLM
    and returns predictable, structured data based on the agent's output_schema.
    """
    payload = {"query": "This is a test query."}
    workflow_name = "test_analysis_workflow"

    # Execute the workflow
    final_context = await run_workflow(workflow_name, payload)

    # --- Assertions on the final context ---

    # 1. Check the output of the first agent (summarizer_agent)
    summary_result = final_context["context"]["summary_result"]
    assert isinstance(summary_result, SummaryOutput)
    # The mock now returns a simple, static string.
    assert summary_result.summary == "Mocked summary"

    # 2. Check the output of the second agent (sentiment_agent)
    # This step runs conditionally, so its presence is a test of the 'when' clause
    sentiment_result = final_context["context"]["sentiment_result"]
    assert isinstance(sentiment_result, SentimentOutput)
    assert sentiment_result.sentiment == "positive"
    assert sentiment_result.rationale == "Mocked rationale"

    # --- Assertions on the rendered output ---
    output = render_workflow_output(workflow_name, final_context)

    assert "Summary: Mocked summary" in output
    assert "Sentiment: positive" in output
