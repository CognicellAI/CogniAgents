# CogniAgents Framework

CogniAgents is a generic, config-driven agentic framework built on PydanticAI and designed to work with OpenAI-compatible endpoints like OpenWebUI. It allows you to define agents, orchestrate them into workflows, and render their outputs using a flexible `config.yaml` file.

## Features

*   **Config-driven**: Define agents, prompts, models, and workflows entirely in `config.yaml`.
*   **OpenAI-compatible**: Seamlessly integrates with OpenWebUI or any other OpenAI-compatible API.
*   **Typed Outputs**: Leverage Pydantic for structured outputs from your agents.
*   **Compositional Workflows**: Chain multiple agents to perform complex tasks.
*   **Templated Rendering**: Use Jinja2 templates to format the final output of your workflows.

## Getting Started

### 1. Prerequisites

*   Python 3.9+
*   An OpenAI-compatible API endpoint (e.g., [OpenWebUI](https://docs.openwebui.com/)). Ensure it's running and accessible.

### 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/cogni-agents.git
    cd cogni-agents
    ```

2.  **Set up a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -e ".[dev]"
    ```
    This installs core dependencies (`PyYAML`, `pydantic`, `pydantic-ai`, `Jinja2`, `python-dotenv`) and development dependencies (`pytest`, `pytest-asyncio`).

### 3. Configuration

The core of CogniAgents is the `config.yaml` file. This file defines your LLM settings, agents, workflows, and output templates.

1.  **Create a `config.yaml` file** in the root of your project. You can use the provided `config.yaml` as a starting point:

    ```yaml
    # config.yaml
    global_llm_settings:
      model: "gemini-2.5-flash" # Replace with your desired default model
      temperature: 0.1

    agents:
      - name: "generic_summarizer"
        title: "Generic Summarizer"
        description: "Summarizes any text content."
        llm_model: "gemini-2.5-flash" # Ensure this model is available in your OpenWebUI setup
        output_schema: "summary"     # Maps to SummaryOutput in cogni_agents/schemas.py
        prompt: |
          Summarize the following content clearly and concisely.
          Do not refer to "this text" or "the document" in your answer.

      - name: "sentiment_analyzer"
        title: "Sentiment Analyzer"
        description: "Classifies sentiment of text."
        llm_model: "sentiment-model" # Ensure this model is available in your OpenWebUI setup
        output_schema: "sentiment"   # Maps to SentimentOutput in cogni_agents/schemas.py
        prompt: |
          Analyze the sentiment of the following content and return:
          - overall sentiment (positive, neutral, negative)
          - a short rationale.

    workflows:
      - name: "summarize_document"
        description: "Summarize arbitrary input text."
        steps:
          - agent: "generic_summarizer"
            input_from: "payload.content"   # Get input from the initial payload's 'content' field
            save_as: "summary"              # Save the agent's output under 'summary' in the workflow context

      - name: "analyze_text_with_sentiment"
        description: "Summarize and analyze sentiment."
        steps:
          - agent: "generic_summarizer"
            input_from: "payload.content"
            save_as: "summary"
          - agent: "sentiment_analyzer"
            input_from: "payload.content" # Can also use payload for subsequent steps
            save_as: "sentiment"

    templates:
      summarize_document: |
        # Summary

        {{ results.summary.summary }}

      analyze_text_with_sentiment: |
        # Analysis Report

        ## Summary
        {{ results.summary.summary }}

        ## Sentiment Analysis
        Overall sentiment: **{{ results.sentiment.sentiment }}**
        Rationale: {{ results.sentiment.rationale }}

    defaults:
      max_tokens: 2048
      language: "en"
    ```

2.  **Specify Configuration File Location (Optional)**:
    By default, CogniAgents looks for `config.yaml` in the current working directory. You can specify an alternative path using the `COGNIA_CONFIG_PATH` environment variable:

    ```bash
    export COGNIA_CONFIG_PATH="/path/to/your/custom_config.yaml"
    # Or for a single command:
    COGNIA_CONFIG_PATH="/path/to/your/custom_config.yaml" python your_script.py
    ```

3.  **Set up API Credentials**:
    CogniAgents uses environment variables for API credentials, which are loaded from a `.env` file if present.
    Create a `.env` file in the root of your project (and ensure it's in your `.gitignore`):

    ```
    # .env
    OPENAI_BASE_URL="http://localhost:8080/v1" # Your OpenWebUI API endpoint
    OPENAI_API_KEY="sk-your-api-key"           # Your API key (can be a dummy value for OpenWebUI if not enforced)
    ```

    Replace the values with your actual OpenWebUI endpoint and API key.

### 4. Defining Output Schemas

Structured outputs are defined using Pydantic models in `cogni_agents/schemas.py`. You can extend this file with your own custom output schemas.

```python
# cogni_agents/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Type, Union

class SummaryOutput(BaseModel):
    summary: str = Field(description="The concise summary of the input text.")

class SentimentOutput(BaseModel):
    sentiment: str = Field(description="The overall sentiment (e.g., positive, neutral, negative).")
    rationale: str = Field(description="A short explanation for the determined sentiment.")

# Add your custom schemas here
# class MyCustomOutput(BaseModel):
#     field1: str
#     field2: int

OUTPUT_SCHEMAS: Dict[str, Type[BaseModel] | Type[str]] = {
    "summary": SummaryOutput,
    "sentiment": SentimentOutput,
    # "my_custom_output": MyCustomOutput,
    # Default to str if a schema name is not found here
}
```

### 5. Running Workflows

You can integrate CogniAgents into your application by importing and using the `run_workflow` and `render_workflow_output` functions.

Here's a simple example of how to run a workflow:

```python
# example_runner.py
import asyncio
import logging
from cogni_agents.workflow_engine import run_workflow, render_workflow_output
from cogni_agents.config_loader import reload_config # Important for hot-reloading config changes

# Configure logging for better visibility
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Optional: Reload config if you've made changes and want them to take effect
    # without restarting the application.
    reload_config()

    workflow_name = "summarize_document"
    payload = {
        "content": "CogniAgents is a powerful framework. It allows developers to define "
                   "complex AI workflows using a simple YAML configuration. This makes "
                   "it highly flexible and easy to adapt to various use cases, from "
                   "summarization to sentiment analysis and beyond. It integrates "
                   "seamlessly with OpenAI-compatible LLM providers like OpenWebUI."
    }

    logger.info(f"Running workflow: {workflow_name}")
    try:
        context = await run_workflow(workflow_name, payload)
        final_output = render_workflow_output(workflow_name, context)

        print("\n--- Workflow Output ---")
        print(final_output)
        print("-----------------------")

        # Example of running another workflow
        workflow_name_sentiment = "analyze_text_with_sentiment"
        payload_sentiment = {
            "content": "I absolutely love using CogniAgents! It's so intuitive and powerful. "
                       "The config-driven approach is a game-changer for rapid prototyping."
        }
        logger.info(f"Running workflow: {workflow_name_sentiment}")
        context_sentiment = await run_workflow(workflow_name_sentiment, payload_sentiment)
        final_output_sentiment = render_workflow_output(workflow_name_sentiment, context_sentiment)

        print("\n--- Sentiment Analysis Workflow Output ---")
        print(final_output_sentiment)
        print("----------------------------------------")

    except Exception as e:
        logger.error(f"An error occurred during workflow execution: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

To run this example:

```bash
python example_runner.py
```

### 6. Development and Testing

#### Running Tests

To run the unit and integration tests:

```bash
pytest tests/
```

#### Hot Reloading Configuration

During development, you can call `cogni_agents.config_loader.reload_config()` to force the framework to re-read `config.yaml` (or the file specified by `COGNIA_CONFIG_PATH`) without restarting your application. Similarly, `cogni_agents.agent_registry.reload_agents()` and `cogni_agents.workflow_engine.reload_workflows()` can be used to refresh agents and workflows.

## Project Structure

```
.
├── cogni_agents/
│   ├── __init__.py
│   ├── agent_registry.py       # Manages loading and caching of CogniAgent instances
│   ├── cogni_agent.py          # Wrapper around PydanticAI Agent
│   ├── config_loader.py        # Loads and parses config.yaml (or COGNIA_CONFIG_PATH)
│   ├── schemas.py              # Defines Pydantic output schemas
│   └── workflow_engine.py      # Orchestrates agent execution based on workflows
├── docs/
│   └── Design.md               # Project design document
├── tests/
│   ├── conftest.py             # Pytest fixtures for common test setup
│   ├── test_agent_registry.py
│   ├── test_cogni_agent.py
│   ├── test_config_loader.py
│   ├── test_integration.py
│   ├── test_workflow_engine.py
│   └── test_config.yaml        # Test-specific configuration file
├── .env.example                # Example .env file (DO NOT COMMIT .env)
├── .gitignore
├── config.yaml                 # Main configuration file (default)
├── pyproject.toml              # Project metadata and dependencies
└── README.md                   # This file
```

## Contributing

Contributions are welcome! Please refer to the `docs/Design.md` and `Roadmap.md` for project vision and planned features.

## License

This project is licensed under the MIT License.
