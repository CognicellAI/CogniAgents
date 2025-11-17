# Core Concepts

CogniAgents is built on a few simple but powerful ideas. Understanding them will help you get the most out of the framework.

## 1. Declarative First

The entire framework is designed around a "declarative first" philosophy. Instead of writing complex Python code to define your agents and workflows, you declare them in a `config.yaml` file.

This makes your systems easier to read, modify, and maintain, even for team members who are not expert developers.

## 2. Agents as Configurable Components

A `CogniAgent` is a self-contained component that wraps an LLM. Its behavior is defined entirely in the `agents` section of your `config.yaml`. Each agent has three key properties:

- **Prompt:** The instructions for the agent. This can be composed from reusable `prompt_components`.
- **Input:** The dynamic data the prompt needs, provided by a workflow step (e.g., `{customer_query}`).
- **Output Schema:** The structure of the agent's response. This can be a simple `str` or a custom Pydantic model you define.

## 3. Workflows as Orchestrators

A workflow is a sequence of steps that orchestrates one or more agents to accomplish a goal.

- **Steps:** Each step in a workflow typically invokes an agent.
- **Context:** The workflow maintains a `context` dictionary. The output of one step can be saved to the context and used as input for a later step.
- **Conditional Logic:** Steps can be executed conditionally using the `when` key, allowing you to build decision-tree-like logic.

## 4. Dynamic Extensibility

The framework is designed to be extended without modifying its core code.

### Custom Schemas

You can define your own Pydantic models for agent outputs in your own Python files. You then register them in your `config.yaml` under the `custom_schemas` section, making them available to any agent.

