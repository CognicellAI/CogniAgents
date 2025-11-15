import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock, mock_open
from cogni_agents.workflow_engine import run_workflow, render_workflow_output
from cogni_agents.config_loader import reload_config
from cogni_agents.agent_registry import reload_agents
from cogni_agents.schemas import SummaryOutput, SentimentOutput
from pydantic_ai import Agent as PydanticAIAgent
from pydantic_ai.models.openai import OpenAIChatModel


# Sample config content for the integration test
INTEGRATION_CONFIG_CONTENT = """
global_llm_settings:
  model: "mock-llm-model"
  temperature: 0.1

agents:
  - name: "integration_summarizer"
    title: "Integration Summarizer"
    description: "Summarizes text for integration test."
    llm_model: "mock-llm-model"
    output_schema: "summary"
    prompt: "Summarize this content."

  - name: "integration_sentiment_analyzer"
    title: "Integration Sentiment Analyzer"
    description: "Analyzes sentiment for integration test."
    llm_model: "mock-llm-model"
    output_schema: "sentiment"
    prompt: "Analyze sentiment."

workflows:
  - name: "integration_summary_workflow"
    description: "A simple summary workflow for integration."
    steps:
      - agent: "integration_summarizer"
        input_from: "payload.text_to_summarize"
        save_as: "final_summary"

  - name: "integration_multi_step_workflow"
    description: "Multi-step workflow for integration."
    steps:
      - agent: "integration_summarizer"
        input_from: "payload.content"
        save_as: "summary_result"
      - agent: "integration_sentiment_analyzer"
        input_from: "results.summary_result.summary" # Input from previous step's output
        save_as: "sentiment_result"

templates:
  integration_summary_workflow: |
    Integration Test Summary: {{ results.final_summary.summary }}

  integration_multi_step_workflow: |
    ## Integration Multi-Step Report
    Summary: {{ results.summary_result.summary }}
    Sentiment: {{ results.sentiment_result.sentiment }} ({{ results.sentiment_result.rationale }})
"""

@pytest.fixture(autouse=True)
def mock_integration_config_file():
    """
    Mocks the config.yaml for integration tests.
    Ensures config and agent registries are reloaded before and after each test.
    """
    reload_config()
    reload_agents() # Also reload agents as they depend on config
    with patch("builtins.open", new_callable=lambda: patch("builtins.open", mock_open(read_data=INTEGRATION_CONFIG_CONTENT)).__enter__()):
        yield
    reload_config()
    reload_agents()


@pytest.fixture
def mock_pydantic_ai_agent_run():
    """
    Mocks the `run` method of PydanticAIAgent to control LLM responses.
    """
    with patch("pydantic_ai.Agent.run", new_callable=AsyncMock) as mock_run:
        # Configure side_effect to return different outputs based on agent's purpose
        def side_effect_func(input_text: str):
            if "Summarize" in input_text: # Heuristic for summarizer agent
                mock_result = MagicMock()
                mock_result.output = SummaryOutput(summary=f"Mocked summary of: {input_text[:20]}...")
                return mock_result
            elif "sentiment" in input_text: # Heuristic for sentiment agent
                mock_result = MagicMock()
                mock_result.output = SentimentOutput(sentiment="positive", rationale="Mocked rationale")
                return mock_result
            else:
                mock_result = MagicMock()
                mock_result.output = f"Mocked generic output for: {input_text[:20]}..."
                return mock_result

        mock_run.side_effect = side_effect_func
        yield mock_run


@pytest.fixture(autouse=True)
def mock_openai_chat_model_init():
    """
    Mocks the OpenAIChatModel constructor to prevent actual API calls.
    """
    with patch("cogni_agents.cogni_agent.OpenAIChatModel") as mock_chat_model:
        mock_chat_model.return_value = MagicMock(spec=OpenAIChatModel)
        yield mock_chat_model


@pytest.mark.asyncio
async def test_integration_simple_summary_workflow(mock_pydantic_ai_agent_run):
    """
    End-to-end test for a simple summary workflow.
    """
    workflow_name = "integration_summary_workflow"
    payload = {"text_to_summarize": "This is a long document that needs to be summarized for testing purposes."}

    # Run the workflow
    context = await run_workflow(workflow_name, payload)

    # Assertions on the context
    assert "payload" in context
    assert "results" in context
    assert context["payload"] == payload
    assert "final_summary" in context["results"]
    assert isinstance(context["results"]["final_summary"], SummaryOutput)
    assert "Mocked summary" in context["results"]["final_summary"].summary

    # Assertions on agent invocation
    mock_pydantic_ai_agent_run.assert_called_once()
    args, kwargs = mock_pydantic_ai_agent_run.call_args
    assert "This is a long document" in args[0]

    # Render the output
    final_output = render_workflow_output(workflow_name, context)
    assert "Integration Test Summary:" in final_output
    assert "Mocked summary" in final_output


@pytest.mark.asyncio
async def test_integration_multi_step_workflow(mock_pydantic_ai_agent_run):
    """
    End-to-end test for a multi-step workflow involving summarization and sentiment analysis.
    """
    workflow_name = "integration_multi_step_workflow"
    payload = {"content": "The product launch was a huge success! Everyone loved it."}

    # Run the workflow
    context = await run_workflow(workflow_name, payload)

    # Assertions on the context
    assert "payload" in context
    assert "results" in context
    assert context["payload"] == payload
    assert "summary_result" in context["results"]
    assert "sentiment_result" in context["results"]

    summary_output = context["results"]["summary_result"]
    sentiment_output = context["results"]["sentiment_result"]

    assert isinstance(summary_output, SummaryOutput)
    assert "Mocked summary" in summary_output.summary
    assert isinstance(sentiment_output, SentimentOutput)
    assert sentiment_output.sentiment == "positive"
    assert sentiment_output.rationale == "Mocked rationale"

    # Assertions on agent invocations
    assert mock_pydantic_ai_agent_run.call_count == 2
    # Check calls in order (or at least inputs)
    call1_input = mock_pydantic_ai_agent_run.call_args_list[0].args[0]
    call2_input = mock_pydantic_ai_agent_run.call_args_list[1].args[0]

    assert "The product launch" in call1_input # Input to summarizer
    assert "Mocked summary" in call2_input # Input to sentiment analyzer (output of summarizer)

    # Render the output
    final_output = render_workflow_output(workflow_name, context)
    assert "## Integration Multi-Step Report" in final_output
    assert "Summary: Mocked summary" in final_output
    assert "Sentiment: positive (Mocked rationale)" in final_output
