# Tutorial: Building an Advanced Customer Support Workflow

This tutorial walks through the `customer_support_router` example, demonstrating how to build a multi-agent workflow that not only routes a customer query but also generates a tailored response using conditional logic.

## Goal

We will build a workflow that:
1.  Analyzes an incoming customer query.
2.  Routes it to the correct virtual department: "Technical Support", "Billing", "Sales", or "General Inquiry".
3.  Invokes a specialized agent for that department to generate a context-aware response.
4.  Presents a final report showing the query, the routing decision, and the generated response.

---

## 1. The Components

This workflow is composed of several reusable and configurable parts defined in `config.yaml`.

### Custom Schema (`SupportRouteOutput`)

First, we need a structured way to capture the routing decision. We define a Pydantic model for this.

**`examples/customer_support_router/custom_schemas.py`:**
```python
from pydantic import BaseModel, Field

class SupportRouteOutput(BaseModel):
    """
    Defines the structured output for the support routing agent.
    """
    department: str = Field(description="The department to route to (e.g., 'Technical Support', 'Billing', 'Sales', 'General Inquiry').")
    reason: str = Field(description="A brief reason for the routing decision.")
```

In `config.yaml`, we register this schema so the framework can use it:
```yaml
custom_schemas:
  support_route: "examples.customer_support_router.custom_schemas.SupportRouteOutput"
```

### Prompt Components

To avoid repeating instructions, we define reusable `prompt_components`. This makes prompts easier to manage and ensures consistency.

```yaml
prompt_components:
  acme_persona: |
    You are a helpful and friendly assistant for Acme Inc. named "Cogni".
    Always be polite and empathetic. Do not make promises you cannot keep.
    Your responses should be concise and to the point.
  summarize_issue: |
    First, acknowledge the user's query.
    Then, briefly summarize the core issue you have identified based on the query.
```

### The Agents

The example uses two types of agents: a single "router" agent and several specialized "responder" agents.

1.  **The Router Agent (`support_router`)**: Its only job is to classify the query. It uses our custom `support_route` schema to ensure its output is structured.

    ```yaml
    - name: support_router
      prompt: |
        You are an AI assistant whose sole purpose is to route customer support queries...
        Choose one of the following departments: "Technical Support", "Billing", "Sales", "General Inquiry".
        Provide a brief reason for your routing decision.
        Customer Query: {customer_query}
      output_schema: "support_route"
    ```

2.  **The Responder Agents (e.g., `technical_support_agent`)**: Each of these agents is an expert in a specific domain. They use the `prompt_components` to craft a high-quality response.

    ```yaml
    - name: technical_support_agent
      prompt: |
        {{ prompt_components.acme_persona }}

        You are a Technical Support Agent.
        {{ prompt_components.summarize_issue }}

        Customer Query:
        {customer_query}
      output_schema: "str" # The final response is a simple string
    ```
    The other agents (`billing_agent`, `sales_agent`, etc.) are defined similarly.

---

## 2. The Workflow (`route_customer_query`)

The workflow orchestrates the agents using conditional logic.

```yaml
workflows:
  - name: route_customer_query
    steps:
      - name: initial_routing
        agent: support_router
        input:
          customer_query: "{{ payload.customer_query }}"
        output_to: routing_decision

      - name: handle_technical_support
        agent: technical_support_agent
        input:
          customer_query: "{{ payload.customer_query }}"
        output_to: final_response
        when: "{{ context.routing_decision.department == 'Technical Support' }}"

      # ... other conditional steps for Billing, Sales, etc. ...
```

Let's break down the logic:
1.  **`initial_routing`**: This first step always runs. It calls the `support_router` agent, passing the user's query from the initial `payload`. The agent's structured output (the `SupportRouteOutput` object) is saved to the workflow's `context` under the key `routing_decision`.
2.  **`handle_technical_support`**: This step is conditional. The `when` expression is evaluated. If the `department` field in the `routing_decision` object from the first step is "Technical Support", this step runs. It calls the `technical_support_agent` and saves its string response to the context as `final_response`.
3.  The other `handle_*` steps work the same way. Because of the `when` conditions, **only one** of the responder agents will ever be executed for a given query.

---

## 3. The Final Output Template

Finally, the `templates` section defines how to present the result after the workflow completes. It uses Jinja2 syntax to pull data from the `payload` and the final `context`.

```yaml
templates:
  route_customer_query: |
    Customer Query: {{ payload.customer_query }}
    ---
    Routing Decision:
    Department: {{ context.routing_decision.department }}
    Reason: {{ context.routing_decision.reason }}
    ---
    Agent Response:
    {{ context.final_response }}
```
This template assembles a clear, final report for the user.

---

## 4. Running the Workflow

You can run the entire workflow with a single CLI command:

```bash
cogni-agents route_customer_query \
  --config-path examples/customer_support_router/config.yaml \
  --payload '{"customer_query": "My internet is down!"}'
```

### Expected Output

The framework will execute the workflow and print the formatted output:

```text
Customer Query: My internet is down!
---
Routing Decision:
Department: Technical Support
Reason: The user is reporting an issue with their internet service being down, which is a technical problem.
---
Agent Response:
Hello! I'm Cogni, and I understand you're having trouble with your internet connection. I've identified that your internet service is currently down. I'm sorry for the inconvenience this is causing. Please stand by while I connect you with a technical support specialist who can assist you further.
```