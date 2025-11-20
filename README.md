# CogniAgents: A YAML-Driven Agent Framework

CogniAgents is a lightweight framework for creating and managing AI agents using a simple, declarative YAML configuration. It is designed to be easy to maintain and extend, allowing you to define agents, tools, and schemas in a single, human-readable file.

## Key Features

*   **YAML-Driven Configuration**: Define your agents, tools, and schemas in a single `config.yaml` file, making it easy to manage and version your AI-native applications.
*   **Extensible Tool System**: Add custom Python functions as tools for your agents to use, or connect to external MCP (Model Context Protocol) servers to leverage existing toolsets.
*   **Structured Output**: Use Pydantic models to define the output schema for your agents, ensuring reliable, structured data from the LLM.
*   **Powered by PydanticAI**: Built on top of the powerful and popular PydanticAI library, giving you the best of both worlds: a simple, declarative interface and a robust, underlying engine.

## Getting Started

### 1. Installation

```bash
pip install cogni-agents
```

### 2. Create a `config.yaml`

Create a `config.yaml` file to define your first agent:

```yaml
global_llm_settings:
  model: "gemini-2.5-flash"

agents:
  - name: hello_agent
    description: "A simple agent that says hello."
    prompt: |
      Say hello to {name}.
    output_schema: "string"
```

### 3. Run Your Agent

Create a Python script to run your agent:

```python
import asyncio
from cogni_agents.cogni_agent import CogniAgent
from cogni_agents.config_loader import set_config_path

# Set the path to your configuration file
set_config_path("config.yaml")

async def main():
    agent = await CogniAgent.from_name("hello_agent")
    result = await agent.invoke({"name": "World"})
    print(result.output)

if __name__ == "__main__":
    asyncio.run(main())
```

## Full Documentation

For more detailed information on how to use CogniAgents, including how to add tools and define custom schemas, please see the [full documentation](docs/index.md).
