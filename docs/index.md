# Welcome to the CogniAgents Framework

**CogniAgents** is a flexible and extensible framework for defining, orchestrating, and executing AI agents and workflows using simple YAML configurations.

It is designed to be:
- **Declarative:** Define complex agentic behavior in easy-to-read YAML files.
- **Extensible:** Bring your own Pydantic schemas and prompt components to customize agent outputs and behavior.
- **Maintainable:** Build reusable components to keep your agent and workflow definitions DRY (Don't Repeat Yourself).

---

## Getting Started

### 1. Installation

Clone the repository and install the framework in editable mode. This also installs the development dependencies needed for documentation.

```bash
git clone https://github.com/your-username/CogniAgents.git
cd CogniAgents
pip install -e ".[dev]"
```

### 2. Configure Environment

Create a `.env` file in the project root to store your LLM API credentials.

```
OPENAI_BASE_URL="http://your-llm-endpoint:port/v1"
OPENAI_API_KEY="your-api-key"
```

### 3. Run an Example

Use the CLI to run the customer support router example.

```bash
cogni-agents route_customer_query \
  --config-path examples/customer_support_router/config.yaml \
  --payload '{"customer_query": "My internet is down!"}'
```

Ready to dive deeper? Check out the **[Core Concepts](core_concepts.md)**.
