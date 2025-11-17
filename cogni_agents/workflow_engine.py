import asyncio
import logging
from typing import Any, Dict, Optional

from jinja2 import Template, Environment, FileSystemLoader

from .config_loader import get_workflow_configs, get_template
from .agent_registry import ensure_agents_loaded, get_agent

logger = logging.getLogger(__name__)

# workflow configs indexed by name for quick lookup
_workflow_by_name: Dict[str, Dict[str, Any]] = {}
_workflows_loaded = False
_lock = asyncio.Lock()


async def load_workflows():
    """
    Loads and indexes workflow configurations from config.yaml.
    This function is idempotent and uses an asyncio lock to prevent race conditions.
    """
    global _workflows_loaded
    if _workflows_loaded:
        logger.debug("Workflows already loaded, skipping.")
        return

    async with _lock:
        if _workflows_loaded:
            logger.debug("Workflows already loaded by another coroutine, skipping.")
            return

        logger.info("Loading workflow configurations...")
        workflow_configs = get_workflow_configs()
        if not workflow_configs:
            logger.warning("No workflow configurations found in config.yaml.")
            _workflows_loaded = True
            return

        for wf_config in workflow_configs:
            name = wf_config.get("name")
            if not name:
                logger.error(f"Workflow configuration missing 'name' field: {wf_config}")
                continue
            _workflow_by_name[name] = wf_config
            logger.debug(f"Workflow '{name}' loaded.")

        _workflows_loaded = True
        logger.info(f"Successfully loaded {len(_workflow_by_name)} workflows.")


async def run_workflow(workflow_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a specified workflow with the given payload.

    Args:
        workflow_name: The name of the workflow to run.
        payload: A dictionary containing the initial input data for the workflow.

    Returns:
        A dictionary containing the final context of the workflow, including results
        from all steps.

    Raises:
        ValueError: If the workflow is not found.
        Exception: For errors during agent invocation.
    """
    await ensure_agents_loaded()
    await load_workflows()

    wf = _workflow_by_name.get(workflow_name)
    if not wf:
        raise ValueError(f"Workflow '{workflow_name}' not found.")

    logger.info(f"Starting workflow '{workflow_name}' with payload: {payload}")
    # The context will hold payload and results from each step
    context: Dict[str, Any] = {"payload": payload, "context": {}}

    for step in wf.get("steps", []):
        agent_name = step.get("agent")
        step_name = step.get("name", agent_name) # Use step name if provided, else agent name
        if not agent_name:
            logger.error(f"Workflow '{workflow_name}' step '{step_name}' missing 'agent' field: {step}")
            continue

        step_input_template = step.get("input", {})
        output_to = step.get("output_to", step_name)

        try:
            agent = get_agent(agent_name)

            # Render input template using current context (payload + previous results)
            # This allows agents to use outputs from previous steps or initial payload
            env = Environment()
            rendered_input: Dict[str, Any] = {}
            for key, value_template in step_input_template.items():
                template = env.from_string(value_template)
                # Pass the entire context (payload and previous step results) to the template
                rendered_input[key] = template.render(payload=context["payload"], context=context["context"])

            logger.debug(f"Invoking agent '{agent_name}' for step '{step_name}' with rendered input: {rendered_input}")

            # Invoke the agent with the rendered input dictionary
            result = await agent.invoke(rendered_input)
            context["context"][output_to] = result
            logger.debug(f"Agent '{agent_name}' result saved as '{output_to}'.")
        except Exception as e:
            logger.error(f"Error in workflow '{workflow_name}' at step '{step_name}' (agent: {agent_name}): {e}")
            raise # Re-raise to stop workflow execution on error

    logger.info(f"Workflow '{workflow_name}' completed.")
    return context


def render_workflow_output(workflow_name: str, context: Dict[str, Any]) -> str:
    """
    Renders the final output of a workflow using a Jinja2 template if available.

    Args:
        workflow_name: The name of the workflow.
        context: The final context dictionary from the workflow execution,
                 containing 'payload' and 'context' (for step results).

    Returns:
        The rendered string output. If no template is found for the workflow,
        it returns a string representation of the workflow results.
    """
    template_str = get_template(workflow_name)
    if not template_str:
        logger.debug(f"No template found for workflow '{workflow_name}'. Returning string representation of results.")
        return str(context.get("context", {}))

    logger.debug(f"Rendering output for workflow '{workflow_name}' using template.")
    try:
        # Pass both payload and the accumulated context (results) to the template
        env = Environment()
        template = env.from_string(template_str)
        return template.render(payload=context.get("payload", {}), context=context.get("context", {}))
    except Exception as e:
        logger.error(f"Error rendering template for workflow '{workflow_name}': {e}")
        # Fallback to string representation of results on template rendering error
        return str(context.get("context", {}))


def reload_workflows():
    """
    Forces a reload of all workflow configurations.
    """
    global _workflow_by_name, _workflows_loaded
    logger.info("Reloading all workflow configurations...")
    _workflow_by_name = {}
    _workflows_loaded = False
