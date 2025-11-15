import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock, mock_open
from cogni_agents.workflow_engine import run_workflow, render_workflow_output
from cogni_agents.config_loader import reload_config
from cogni_agents.agent_registry import reload_agents
from cogni_agents.schemas import SummaryOutput, SentimentOutput
from pydantic_ai import Agent as PydanticAIAgent
from pydantic_ai.models.openai import OpenAIChatModel


# mock_config_content, mock_pydantic_ai_agent_run, mock_openai_chat_model_init
# are now provided by conftest.py

@pytest.mark.asyncio
async def test_integration_simple_summary_workflow(mock_config_content, mock_pydantic_ai_agent_run, mock_openai_chat_model_init):
    """
    End-to-end test for a simple summary workflow.
    """
    workflow_name = "test_workflow_1" # Using workflow from conftest.py sample
    payload = {"text": "This is a long document that needs to be summarized for testing purposes."}

    # Run the workflow
    context = await run_workflow(workflow_name, payload)

    # Assertions on the context
    assert "payload" in context
    assert "results" in context
    assert context["payload"] == payload
    assert "step1_result" in context["results"]
    assert isinstance(context["results"]["step1_result"], SummaryOutput)
    assert "Mocked summary" in context["results"]["step1_result"].summary

    # Assertions on agent invocation
    mock_pydantic_ai_agent_run.assert_called_once()
    # The first arg to the patched method is the `self` instance. The second is the input text.
    args, kwargs = mock_pydantic_ai_agent_run.call_args
    assert "This is a long document" in args[1]

    # Render the output
    final_output = render_workflow_output(workflow_name, context)
    assert "Summary: Mocked summary" in final_output


@pytest.mark.asyncio
async def test_integration_multi_step_workflow(mock_config_content, mock_pydantic_ai_agent_run, mock_openai_chat_model_init):
    """
    End-to-end test for a multi-step workflow involving summarization and sentiment analysis.
    """
    workflow_name = "multi_step_workflow" # Using workflow from conftest.py sample
    payload = {"content": "The product launch was a huge success! Everyone loved it."}

    # Run the workflow
    context = await run_workflow(workflow_name, payload)

    # Assertions on the context
    assert "payload" in context
    assert "results" in context
    assert context["payload"] == payload
    assert "summary" in context["results"] # Changed from summary_result
    assert "sentiment" in context["results"] # Changed from sentiment_result

    summary_output = context["results"]["summary"] # Changed from summary_result
    sentiment_output = context["results"]["sentiment"] # Changed from sentiment_result

    assert isinstance(summary_output, SummaryOutput)
    assert "Mocked summary" in summary_output.summary
    assert isinstance(sentiment_output, SentimentOutput)
    assert sentiment_output.sentiment == "positive"
    assert sentiment_output.rationale == "Mocked rationale"

    # Assertions on agent invocations
    assert mock_pydantic_ai_agent_run.call_count == 2
    # The calls are on the same mock instance, so we check call_args_list
    call1_input = mock_pydantic_ai_agent_run.call_args_list[0].args[1]
    call2_input = mock_pydantic_ai_agent_run.call_args_list[1].args[1]

    assert "The product launch" in call1_input # Input to summarizer
    assert "Mocked summary" in call2_input # Input to sentiment analyzer (output of summarizer)

    # Render the output
    final_output = render_workflow_output(workflow_name, context)
    assert "## Multi-Step Report" in final_output
    assert "Summary: Mocked summary" in final_output
    assert "Sentiment: positive" in final_output
