# Customer Support Router Example

This example demonstrates how to build a decision-tree-like workflow using CogniAgents, where the output of one agent dictates the subsequent path of execution. The use case is a customer support system that routes incoming queries to the most appropriate specialized agent.

## Use Case

In a customer support scenario, efficiently directing a customer's query to the right department or specialist is crucial for quick resolution and customer satisfaction. This example simulates an AI-powered router that analyzes a customer's initial message and makes a routing decision. Based on this decision, a specific "department agent" then provides a tailored response.

## How CogniAgents are Used

This example defines a workflow named `route_customer_query` which orchestrates several `CogniAgent` instances:

1.  **`support_router` (Decision Agent)**:
    *   **Purpose**: To analyze the initial customer query and determine the most suitable department for handling it.
    *   **Configuration**: Defined in `config.yaml` with a prompt that guides it to classify the query into one of predefined departments ("Technical Support", "Billing", "Sales", "General Inquiry"). It uses a new Pydantic schema, `SupportRouteOutput`, to ensure its output is structured with a `department` and a `reason`.
    *   **Input**: The raw `customer_query`.
    *   **Output**: A structured object (`SupportRouteOutput`) containing the chosen `department` and the `reason` for the decision. This output is saved to `context.routing_decision`.

2.  **Specialized Agents (Action Agents)**:
    *   `technical_support_agent`
    *   `billing_agent`
    *   `sales_agent`
    *   `general_inquiry_agent`
    *   **Purpose**: Each of these agents simulates the response of a specific department. They are designed to acknowledge the query and summarize the issue from their departmental perspective.
    *   **Configuration**: Each has a distinct prompt tailored to its role. They all output a simple `str` (string) response.
    *   **Input**: The raw `customer_query`.
    *   **Output**: A string containing the agent's simulated response. This output is saved to `context.final_response`.

### Workflow Logic (`route_customer_query`):

The workflow `route_customer_query` is structured to implement the decision tree:

*   **Step 1 (`initial_routing`)**: The `support_router` agent is invoked first. Its structured output (`routing_decision`) is crucial for the subsequent steps.
*   **Conditional Steps**: Following the `initial_routing` step, there are multiple steps, each corresponding to a specialized agent. Each of these steps includes a `when` condition. For example:
    ```yaml
    - name: handle_technical_support
      agent: technical_support_agent
      input:
        customer_query: "{{ payload.customer_query }}"
      output_to: final_response
      when: "{{ context.routing_decision.department == 'Technical Support' }}"
    ```
    This `when` condition ensures that `handle_technical_support` is only executed if the `department` identified by the `support_router` is 'Technical Support'. Only one of these conditional steps will execute for any given query, effectively creating a decision path.

Finally, a Jinja2 template renders a comprehensive report, showing the original query, the routing decision, and the response from the chosen specialized agent.

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
    cd examples/customer_support_router
    ```

4.  **Run the script**:
    ```bash
    python run_router.py
    ```

You should see log messages indicating the workflow's progress for several different customer queries, followed by the routing decision and the simulated agent response for each.
