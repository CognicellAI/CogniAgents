# Customer Review Analysis Example

This example demonstrates how to use CogniAgents to analyze customer reviews. It showcases a simple workflow that leverages two distinct AI agents: one for summarizing the review and another for determining its sentiment.

## Use Case

The primary goal is to process raw customer feedback and extract actionable insights. This is a common task in product management, customer service, and marketing to quickly understand customer satisfaction and identify areas for improvement.

## How CogniAgents are Used

This example defines a workflow named `analyze_customer_review` which orchestrates two `CogniAgent` instances:

1.  **`review_summarizer`**:
    *   **Purpose**: To condense a lengthy customer review into its core positive and negative points.
    *   **Configuration**: Defined in `config.yaml` within this directory, with a specific prompt instructing it to extract bullet points for positive and negative aspects. It uses the `SummaryOutput` schema (defined in `cogni_agents/schemas.py`) to ensure structured output.
    *   **Input**: The raw customer review text.
    *   **Output**: A structured object containing lists of positive and negative aspects.

2.  **`review_sentiment_analyzer`**:
    *   **Purpose**: To classify the overall sentiment of the customer review (positive, negative, or neutral) and provide a brief explanation.
    *   **Configuration**: Defined in `config.yaml` within this directory, with a prompt focused on sentiment classification. It uses the `SentimentOutput` schema (defined in `cogni_agents/schemas.py`) for structured output.
    *   **Input**: The raw customer review text.
    *   **Output**: A structured object containing the sentiment label and an explanation.

The `analyze_customer_review` workflow in `config.yaml` defines the sequence of these agents:
*   It first runs `review_summarizer`, storing its output in the workflow context under `summary_result`.
*   Then, it runs `review_sentiment_analyzer`, storing its output under `sentiment_result`.

Finally, a Jinja2 template is used to render a human-readable output that combines the results from both agents.

## Running the Example

To run this example, follow these steps:

1.  **Ensure dependencies are installed**:
    If you haven't already, install the necessary Python packages. From the project root, you can typically run:
    ```bash
    pip install -e ".[dev]"
    ```
    This should install `pyyaml`, `pydantic-ai`, `openai`, `jinja2`, `python-dotenv`, and `pytest`.

2.  **Set up your LLM API Key and Base URL**:
    Create a `.env` file in your **project root directory** (e.g., `CogniAgents/.env`) and add your LLM provider credentials. For OpenAI-compatible APIs (like OpenWebUI, LiteLLM, or OpenAI itself):
    ```
    OPENAI_BASE_URL="http://your-llm-endpoint:port/v1" # e.g., http://localhost:8080/v1 for OpenWebUI
    OPENAI_API_KEY="sk-your-api-key" # This can be a dummy key for local LLMs if not required
    ```
    The `cogni_agents/config_loader.py` automatically loads environment variables from `.env`.

3.  **Navigate to the example directory**:
    From the project root, change into this example's directory:
    ```bash
    cd examples/customer_review_analysis
    ```

4.  **Run the script**:
    ```bash
    python run_analysis.py
    ```

You should see log messages indicating the workflow's progress, followed by the structured analysis of the customer review printed to the console.
