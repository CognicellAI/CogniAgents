# CogniAgents Implementation Roadmap

This document outlines the planned phases and key tasks for implementing the CogniAgents framework, based on the `docs/Design.md` document.

## Phase 1: Core Framework (MVP)

**Goal:** Establish the foundational components for a functional, config-driven agentic framework.

### 1.1 Configuration Management

*   **Task:** Implement `Config Loader` to read `config.yaml`.
    *   Sub-task: Load `global_llm_settings`.
    *   Sub-task: Load `agents` definitions.
    *   Sub-task: Load `workflows` definitions.
    *   Sub-task: Load `templates` definitions.
*   **Task:** Implement basic Pydantic validation for `config.yaml` structure (optional but recommended in design).
*   **Task:** Create `OUTPUT_SCHEMAS` registry (mapping logical names to Pydantic models/`str`).

### 1.2 Agent Core

*   **Task:** Implement `CogniAgent` wrapper class.
    *   Sub-task: Initialize `PydanticAIAgent` with `OpenAIChatModel`.
    *   Sub-task: Handle `output_type` mapping from `output_schema_name`.
    *   Sub-task: Implement `_build_instructions` (initial simple prompt).
    *   Sub-task: Implement `async invoke` method.
*   **Task:** Implement `Agent Registry`.
    *   Sub-task: `ensure_agents_loaded` with async lock for lazy/eager loading.
    *   Sub-task: `get_agent` to retrieve initialized `CogniAgent` instances.

### 1.3 Workflow Engine

*   **Task:** Implement `Workflow Engine` core logic.
    *   Sub-task: `load_workflows` to index workflow configs.
    *   Sub-task: `run_workflow` to orchestrate agent execution.
    *   Sub-task: Implement `_resolve_path` for input mapping (`payload.content`).
    *   Sub-task: Manage `context` object for intermediate results.

### 1.4 Rendering Layer

*   **Task:** Implement `render_workflow_output`.
    *   Sub-task: Integrate Jinja2 for template rendering.
    *   Sub-task: Pass `workflow outputs` and `input payload` to template.
    *   Sub-task: Handle cases where no template is defined (default to string conversion).

### 1.5 Integration & Testing

*   **Task:** Set up basic environment variables for OpenWebUI (`OPENAI_BASE_URL`, `OPENAI_API_KEY`).
*   **Task:** Create example `config.yaml` with `generic_summarizer` and `summarize_document` workflow.
*   **Task:** Develop unit tests for `Config Loader`, `CogniAgent`, `Agent Registry`, `Workflow Engine`, and `Rendering Layer`.
*   **Task:** Create an end-to-end integration test for a simple workflow.

## Phase 2: Enhancements & Robustness

**Goal:** Improve flexibility, error handling, and add initial advanced features.

### 2.1 Config & Agent Improvements

*   **Task:** Enhance `_build_instructions` in `CogniAgent` to dynamically enrich prompts with schema hints or other context.
*   **Task:** Implement more robust config validation (e.g., ensure referenced agents/schemas exist).
*   **Task:** Add support for `defaults` section in `config.yaml` (e.g., `max_tokens`, `language`).

### 2.2 Workflow Engine Advanced Features

*   **Task:** Implement **Parallel step execution** (allow `parallel: true` in workflow steps).
    *   Sub-task: Modify `run_workflow` to use `asyncio.gather` for parallel steps.
*   **Task:** Improve error handling and logging within the workflow execution.
*   **Task:** Add more sophisticated input resolution (e.g., combining multiple inputs).

### 2.3 Documentation & Examples

*   **Task:** Expand `docs/Design.md` with more detailed explanations where necessary.
*   **Task:** Create a `README.md` for the project with setup and usage instructions.
*   **Task:** Provide more example `config.yaml` workflows (e.g., `analyze_text_with_sentiment`, `review_code_snippet`).
*   **Task:** Add example Pydantic output schemas.

## Phase 3: Advanced Capabilities & Developer Experience

**Goal:** Introduce more powerful agentic patterns and improve the developer workflow.

### 3.1 Agent Tooling

*   **Task:** Integrate **Tool-using agents** (using PydanticAI tools for external data).
    *   Sub-task: Define how tools are declared in `config.yaml`.
    *   Sub-task: Implement tool registration and invocation within `CogniAgent`.

### 3.2 Scalability & Deployment

*   **Task:** Explore options for **Long-term memory and retrieval-augmented generation** (RAG). (Non-goal for v1, but important for future).
*   **Task:** Investigate deployment strategies (e.g., Docker, serverless functions).

### 3.3 Developer Experience

*   **Task:** Implement **Hot reload in dev** for `config.yaml` changes.
*   **Task:** Develop a CLI for interacting with CogniAgents (e.g., `cogniagents run <workflow> --payload <json>`).

## Phase 4: Future Vision (Beyond v1)

**Goal:** Explore more complex features and broader applicability.

*   **Task:** Implement **Multi-tenant management** (per-tenant configs).
*   **Task:** Design and potentially build a **Production UI for editing config**.
*   **Task:** Explore integration with other LLM providers beyond OpenAI-compatible endpoints.
*   **Task:** Advanced monitoring and observability for agent execution.

---

**Note:** This roadmap is a living document and may be adjusted based on feedback, priorities, and new insights during development.
