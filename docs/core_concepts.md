# Core Concepts

The CogniAgents framework is built on a few fundamental concepts that work together to create powerful, configuration-driven AI systems. Understanding these concepts is key to using the framework effectively.

---

## 1. The Configuration File

The heart of any CogniAgents project is the central YAML configuration file (e.g., `config.yaml`). This file declaratively defines all the components of your system. It acts as the single source of truth for your agents and workflows.

A typical configuration file has the following top-level sections:

- `global_llm_settings`: Default values for the LLM that can be inherited by agents.
- `prompt_components`: Reusable snippets of text that can be included in agent prompts.
- `custom_schemas`: Pointers to custom Pydantic models for structured agent outputs.
- `agents`: A list of all the individual AI agents you want to define.
- `workflows`: A list of multi-step processes that orchestrate one or more agents.
- `templates`: A dictionary of Jinja2 templates for formatting workflow outputs.

## 2. Agents

An **Agent** is the basic building block of the framework. It is a specialized AI entity designed to perform a single, well-defined task. For example, you might have an agent that summarizes text, another that analyzes sentiment, and a third that categorizes customer support tickets.

Under the hood, a `CogniAgent` is a wrapper around a `PydanticAIAgent`. It is defined in the `agents` section of your `config.yaml`.

### Example Agent Definition:

