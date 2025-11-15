import asyncio
import logging
from typing import Any, Dict, Optional

from jinja2 import Template

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
    context: Dict[str, Any] = {"payload": payload, "results": {}}

    for step in wf.get("steps", []):
        agent_name = step.get("agent")
        if not agent_name:
            logger.error(f"Workflow '{workflow_name}' step missing 'agent' field: {step}")
            continue

        input_path = step.get("input_from", "payload.content")
        save_as = step.get("save_as", agent_name)

        try:
            agent = get_agent(agent_name)
            # Resolve input from context via a simple dotted path
            input_text = _resolve_path(context, input_path)
            logger.debug(f"Invoking agent '{agent_name}' for step '{save_as}' with input from '{input_path}'.")

            result = await agent.invoke(input_text, context=context)
            context["results"][save_as] = result
            logger.debug(f"Agent '{agent_name}' result saved as '{save_as}'.")
        except Exception as e:
            logger.error(f"Error in workflow '{workflow_name}' at step '{agent_name}': {e}")
            raise # Re-raise to stop workflow execution on error

    logger.info(f"Workflow '{workflow_name}' completed.")
    return context


def _resolve_path(ctx: Dict[str, Any], path: str) -> Any:
    """
    Resolves a value from a dictionary or Pydantic model using a dotted path string.

    Args:
        ctx: The dictionary (context) to resolve the path from.
        path: The dotted path string (e.g., "payload.content", "results.summary.summary").

    Returns:
        The value found at the specified path.

    Raises:
        KeyError: If any part of the path does not exist in a dictionary.
        AttributeError: If any part of the path does not exist as an attribute on a Pydantic model.
        TypeError: If an intermediate part of the path is not a dictionary or Pydantic model.
    """
    parts = path.split(".")
    val: Any = ctx
    for i, p in enumerate(parts):
        if isinstance(val, dict):
            if p in val:
                val = val[p]
            else:
                raise KeyError(f"Path '{path}' not found. Missing key '{p}' at level {i} in context.")
        elif hasattr(val, p): # Handle Pydantic models
            val = getattr(val, p)
        else:
            raise TypeError(f"Cannot resolve path '{path}'. '{'.'.join(parts[:i])}' is not a dictionary or Pydantic model.")
    return val

def render_workflow_output(workflow_name: str, context: Dict[str, Any]) -> str:
    """
    Renders the final output of a workflow using a Jinja2 template if available.

    Args:
        workflow_name: The name of the workflow.
        context: The final context dictionary from the workflow execution,
                 containing 'payload' and 'results'.

    Returns:
        The rendered string output. If no template is found for the workflow,
        it returns a string representation of the workflow results.
    """
    template_str = get_template(workflow_name)
    if not template_str:
        logger.debug(f"No template found for workflow '{workflow_name}'. Returning string representation of results.")
        return str(context.get("results", {}))

    logger.debug(f"Rendering output for workflow '{workflow_name}' using template.")
    try:
        template = Template(template_str)
        # Pass both results and payload to the template context
        return template.render(results=context.get("results", {}), payload=context.get("payload", {}))
    except Exception as e:
        logger.error(f"Error rendering template for workflow '{workflow_name}': {e}")
        # Fallback to string representation of results on template rendering error
        return str(context.get("results", {}))


def reload_workflows():
    """
    Forces a reload of all workflow configurations.
    """
    global _workflow_by_name, _workflows_loaded
    logger.info("Reloading all workflow configurations...")
    _workflow_by_name = {}
    _workflows_loaded = False
