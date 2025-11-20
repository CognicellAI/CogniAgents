# Welcome to CogniAgents

**CogniAgents** is a YAML-driven framework for creating and managing AI agents. It is designed to be simple, maintainable, and extensible, allowing you to build powerful AI-native applications with just a `config.yaml` file.

---

## About the Framework

CogniAgents is built on the idea that the core components of an AI application—agents, tools, and schemas—should be defined in a declarative, human-readable format. This makes it easy to manage your application's configuration, version it with Git, and collaborate with your team.

At its core, CogniAgents uses the powerful [PydanticAI](https://github.com/pydantic/pydantic-ai) library to handle the interaction with the LLM, giving you a robust and reliable engine for your agents.

---

## Getting Started

Getting started with CogniAgents is easy. Here are the basic steps to create and run your first agent.

### 1. Installation

```bash
pip install cogni-agents
```

### 2. Create Your `config.yaml`

Create a `config.yaml` file in the root of your project:

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

This configuration defines a single agent named `hello_agent` that takes a `name` as input and returns a string.

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

When you run this script, you should see the following output:

```
Hello, World!
```

---

## Next Steps

Now that you have created your first agent, you are ready to explore the more advanced features of the CogniAgents framework:

*   **[Core Concepts](core_concepts.md)**: Learn about the fundamental building blocks of the framework, including agents, tools, and schemas.
*   **[Adding Tools](guides/adding_tools.md)**: Discover how to add custom Python functions as tools for your agents to use.
*   **[Built-in Schemas](guides/built_in_schemas.md)**: See the list of built-in schemas that you can use for structured output.
