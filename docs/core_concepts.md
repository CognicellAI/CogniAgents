# Core Concepts

The CogniAgents framework is built on a few fundamental concepts that work together to create powerful, configuration-driven AI systems. Understanding these concepts is key to using the framework effectively.

---

## 1. The Configuration File (`config.yaml`)

The `config.yaml` file is the heart of a CogniAgents application. It is where you define all the components of your system in a declarative, human-readable format. A typical configuration file has the following top-level sections:

*   `global_llm_settings`: Default values for the LLM that can be inherited by agents.
*   `agents`: A list of all the individual AI agents you want to define.
*   `custom_schemas`: Pointers to custom Pydantic models for structured agent outputs.
*   `custom_tools`: Pointers to custom Python functions that can be used as tools by agents.
*   `mcp_servers`: Configuration for any MCP (Model Context Protocol) servers that provide additional tools as toolsets.
*   `prompt_components`: Reusable snippets of text that can be included in agent prompts.

---

## 2. Agents

An **Agent** is the basic building block of the framework. It is a specialized AI entity designed to perform a single, well-defined task. For example, you might have an agent that summarizes text, another that analyzes sentiment, and a third that categorizes customer support tickets.

An agent is defined in the `agents` section of your `config.yaml`.

### Example Agent Definition:

```yaml
agents:
  - name: sentiment_analyzer
    description: "Analyzes the sentiment of a customer review."
    llm:
      temperature: 0.0
    prompt: |
      Analyze the sentiment of the following text and classify it as 'positive', 'negative', or 'neutral'.
      Provide a brief justification for your classification.
      Text: {text_to_analyze}
    output_schema: "SentimentOutput" # References a built-in or custom schema
```

### Key Agent Properties:

*   `name`: A unique identifier for the agent.
*   `description`: A brief explanation of what the agent does.
*   `llm`: Agent-specific settings for the LLM, which override the `global_llm_settings`.
*   `prompt`: The instructions for the agent, including placeholders for input.
*   `output_schema`: The name of the schema that defines the agent's output structure.
*   `tools`: A list of the names of the local custom tools that the agent can use.
*   `toolsets`: A list of the names of the MCP servers that the agent can use as toolsets.

---

## 3. Schemas

A **Schema** defines the structure of an agent's output. By enforcing a schema, you ensure that the LLM's response is predictable, structured, and easy to work with in your application. Schemas are defined using Pydantic models.

The framework includes several [built-in schemas](guides/built_in_schemas.md), but you can easily define your own.

### Custom Schema Definition:

To use a custom schema, you define it in a Python file and reference it from your `config.yaml`.

**`my_app/schemas.py`:**

```python
from pydantic import BaseModel, Field

class SupportRoute(BaseModel):
    department: str = Field(description="The department to route to (e.g., 'Billing', 'Technical Support', 'Sales').")
    urgency: int = Field(description="An urgency score from 1 to 5.")
```

**`config.yaml`:**

```yaml
custom_schemas:
  support_route_schema: "my_app.schemas.SupportRoute"

agents:
  - name: support_router
    ...
    output_schema: support_route_schema # Use the custom schema
```

---

## 4. Tools and Toolsets

**Tools** and **Toolsets** are how you give your agents the ability to interact with the outside world. They can be used to retrieve information, perform calculations, or trigger external processes.

*   **Tools**: A `tool` is a single, callable Python function that you define locally in your project.
*   **Toolsets**: A `toolset` is a collection of tools that are exposed by an MCP server.

### Custom Tool Definition:

**`my_app/tools.py`:**

```python
def get_current_time() -> str:
    """Returns the current time."""
    from datetime import datetime
    return datetime.now().isoformat()
```

**`config.yaml`:**

```yaml
custom_tools:
  get_time: "my_app.tools.get_current_time"

agents:
  - name: time_agent
    ...
    tools:
      - get_time
```

### MCP Toolset Definition:

**`config.yaml`:**

```yaml
mcp_servers:
  remote_fetcher:
    type: "streamable-http"
    url: "https://remote.mcpservers.org/fetch/mcp"

agents:
  - name: fetcher_agent
    ...
    toolsets:
      - remote_fetcher
```

---

## 5. Prompt Components

**Prompt Components** are reusable pieces of text that help you keep your prompts DRY (Don't Repeat Yourself). You can define a component once and reference it in multiple agent prompts.

### Example Prompt Component:

**`config.yaml`:**

```yaml
prompt_components:
  politeness_clause: "Be polite and professional in your response."

agents:
  - name: sentiment_analyzer
    prompt: |
      Analyze the sentiment of the following text.
      {{ prompt_components.politeness_clause }}
```
