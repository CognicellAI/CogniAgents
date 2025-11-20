# Guide: Adding Tools to Agents

This guide explains how to add functionality to your agents by using local custom tools and by connecting to MCP (Model Context Protocol) servers.

---

## Prerequisites

Before you begin, you should have a basic CogniAgents application set up with a `config.yaml` file and a Python script to run your agents. If you haven't done this yet, please see the [Getting Started](index.md) guide.

---

## Tools vs. Toolsets

In the CogniAgents framework, `tools` and `toolsets` are distinct concepts:

*   **Tools**: A `tool` is a single, callable Python function that you define locally in your project. Each tool is registered individually in the `custom_tools` section of your `config.yaml` and is added to an agent's `tools` list.

*   **Toolsets**: A `toolset` is a collection of tools that are exposed by an MCP server. You define the connection to the MCP server in the `mcp_servers` section of your `config.yaml`, and you add the server to an agent's `toolsets` list. The agent can then access all the tools provided by that server.

In short, `tools` are for a la carte, local functions, while `toolsets` are for consuming tools from an external MCP server.

---

## Adding Local Custom Tools

Here’s how to create and add a local custom tool to an agent.

### 1. Create a Custom Tool

A tool is a simple Python function. Let's create a tool that retrieves the current weather for a given location.

Create a file, for example, `my_app/tools.py`:

```python
import random

def get_current_weather(location: str) -> str:
    """Gets the current weather for a given location."""
    if "tokyo" in location.lower():
        return f"The current weather in Tokyo is 20°C and sunny."
    elif "san francisco" in location.lower():
        return f"The current weather in San Francisco is 15°C and foggy."
    else:
        return f"The current weather in {location} is {random.randint(10, 30)}°C."

```

### 2. Register the Tool

Now, let's register our tool in the `config.yaml` file.

```yaml
custom_tools:
  weather_tool: "my_app.tools:get_current_weather"
```

### 3. Use the Tool in an Agent

Finally, we can use the tool in an agent by adding the tool's name to the `tools` list in the agent's configuration.

```yaml
agents:
  - name: weather_agent
    description: "An agent that can retrieve the current weather."
    prompt: |
      What is the current weather in {location}?
    tools:
      - weather_tool
    output_schema: "string"
```

### 4. Putting It All Together

Here is the complete `config.yaml` and `run_agent.py` for this example:

**`config.yaml`:**

```yaml
global_llm_settings:
  model: "gemini-2.5-flash"

custom_tools:
  weather_tool: "my_app.tools:get_current_weather"

agents:
  - name: weather_agent
    description: "An agent that can retrieve the current weather."
    prompt: |
      What is the current weather in {location}?
    tools:
      - weather_tool
    output_schema: "string"
```

**`run_agent.py`:**

```python
import asyncio
from cogni_agents.cogni_agent import CogniAgent
from cogni_agents.config_loader import set_config_path

# Set the path to your configuration file
set_config_path("config.yaml")

async def main():
    agent = await CogniAgent.from_name("weather_agent")
    result = await agent.invoke({"location": "San Francisco"})
    print(result.output)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Connecting to MCP Servers

Here’s how to connect to an MCP server and use its tools as a toolset.

### 1. Configure the MCP Server

First, you need to add an `mcp_servers` section to your `config.yaml` file.

```yaml
mcp_servers:
  my_mcp_server:
    type: "streamable-http"
    url: "https://remote.mcpservers.org/fetch/mcp"
```

### 2. Use the MCP Toolset in an Agent

Next, you can add the MCP server to an agent's `toolsets` list:

```yaml
agents:
  - name: my_agent
    description: "An agent that can use tools from an MCP server."
    prompt: |
      Fetch the content of {url}
    toolsets:
      - my_mcp_server
    output_schema: "string"
```

### 3. Putting It All Together

Here is the complete `config.yaml` and `run_agent.py` for this example:

**`config.yaml`:**

```yaml
global_llm_settings:
  model: "gemini-2.5-flash"

mcp_servers:
  my_mcp_server:
    type: "streamable-http"
    url: "https://remote.mcpservers.org/fetch/mcp"

agents:
  - name: my_agent
    description: "An agent that can use tools from an MCP server."
    prompt: |
      Fetch the content of {url}
    toolsets:
      - my_mcp_server
    output_schema: "string"
```

**`run_agent.py`:**

```python
import asyncio
from cogni_agents.cogni_agent import CogniAgent
from cogni_agents.config_loader import set_config_path

# Set the path to your configuration file
set_config_path("config.yaml")

async def main():
    agent = await CogniAgent.from_name("my_agent")
    result = await agent.invoke({"url": "http://example.com"})
    print(result.output)

if __name__ == "__main__":
    asyncio.run(main())
```
