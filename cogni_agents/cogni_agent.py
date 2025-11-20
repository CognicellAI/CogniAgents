from __future__ import annotations

import logging
from typing import Any, Dict, Type, cast

try:
    from jinja2 import Environment
    jinja2_available = True
except ImportError:
    jinja2_available = False
from pydantic_ai import Agent as PydanticAIAgent
from pydantic_ai.models.openai import OpenAIChatModel

from .config_loader import get_global_llm_settings, get_prompt_components
from .schemas import get_schema
from .tool_registry import get_tools_and_toolsets


logger = logging.getLogger(__name__)

class CogniAgent:
    """
    A wrapper around PydanticAIAgent that handles configuration-driven agent creation.
    It maps config entries to PydanticAI agent parameters, including dynamic output types.
    """
    def __init__(self, agent_config: Dict[str, Any]):
        """Initializes a CogniAgent from a configuration dictionary."""
        self.name = agent_config["name"]
        self.description = agent_config.get("description")
        self.output_schema_name = agent_config.get("output_schema")

        self.raw_prompt = agent_config["prompt"]
        self.prompt = self._format_prompt(self.raw_prompt, get_prompt_components(), {})

        # Merge global and agent-specific LLM settings
        global_settings = get_global_llm_settings()
        agent_llm_config = agent_config.get("llm", {})
        final_llm_settings = {**global_settings, **agent_llm_config}

        # Extract model name, which is a special parameter for the constructor
        model_name = final_llm_settings.pop("model", None)
        if not model_name:
            raise ValueError(
                f"Agent '{self.name}' missing LLM model. "
                "Specify 'model' in the agent's 'llm' block or in 'global_llm_settings'."
            )

        # Resolve the output type from the dynamic schema registry
        self.output_type: Type[Any] = get_schema(self.output_schema_name)

        # Get the tools and toolsets for the agent
        tool_names = agent_config.get("tools", [])
        toolset_names = agent_config.get("toolsets", [])
        tools, toolsets = get_tools_and_toolsets(tool_names, toolset_names)
        tool_names = [tool.__name__ for tool in tools]
        toolset_names = agent_config.get("toolsets", [])

        # Initialize the underlying PydanticAI components
        chat_model = OpenAIChatModel(model_name=model_name)

        # The remaining settings (temperature, etc.) are passed to the agent
        # The `llm` (chat_model) is passed as a positional argument, not a keyword argument.
        self.agent = PydanticAIAgent(
            chat_model,
            instructions=self._build_instructions(),
            output_type=self.output_type,
            tools=tools,
            toolsets=toolsets,
            model_settings=cast(Dict[str, Any], final_llm_settings),
        )

        logger.info(
            f"Initialized CogniAgent '{self.name}' with model='{model_name}', "
            f"output_type={self.output_type.__name__ if hasattr(self.output_type, '__name__') else str(self.output_type)}, "
            f"tools={tool_names}, "
            f"toolsets={toolset_names}"
        )

    def _format_prompt(self, raw_prompt: str, prompt_components: Dict[str, str], input_data: Dict[str, Any]) -> str:
        """Formats the prompt, first with Jinja2 and then with basic string formatting."""
        if jinja2_available:
            try:
                env = Environment()
                template = env.from_string(raw_prompt)
                return template.render(prompt_components=prompt_components, **input_data)
            except Exception as e:
                logger.warning(f"Jinja2 rendering failed for agent '{self.name}': {e}. Falling back to basic formatting.")
                return raw_prompt.format(**input_data)
        else:
            return raw_prompt.format(**input_data)

    def _build_instructions(self) -> str:
        """
        Builds the instructions for the PydanticAI agent.
        This method can be extended to dynamically enrich the prompt with schema hints
        or other context based on the output_type.
        """
        # For now, it simply returns the configured prompt.
        # Future enhancement: Add schema introspection here.
        return self.prompt

    @classmethod
    async def from_name(cls, name: str) -> CogniAgent:
        """
        Factory method to create a CogniAgent instance from its registered name.

        Args:
            name: The name of the agent to retrieve.

        Returns:
            An instance of the CogniAgent.

        Raises:
            ValueError: If the agent with the given name is not found.
        """
        from .agent_registry import get_agent, ensure_agents_loaded
        await ensure_agents_loaded()
        agent = get_agent(name)
        if not agent:
            raise ValueError(f"Agent '{self.name}' not found.")
        return agent

    async def invoke(self, input_data: Dict[str, Any]) -> Any:
        """
        Invokes the underlying PydanticAI agent with the given input data.

        Args:
            input_data: A dictionary containing the input for the agent.
                        The keys in this dictionary should correspond to placeholders
                        in the agent's prompt.

        Returns:
            The structured output from the agent, or a string if no schema is defined.
        """
        formatted_prompt = self._format_prompt(self.raw_prompt, get_prompt_components(), input_data)

        logger.debug(f"Invoking agent '{self.name}' with formatted prompt: {formatted_prompt[:200]}...")
        try:
            # Pass the *formatted_prompt* as the single input string to the PydanticAIAgent's run method
            result = await self.agent.run(formatted_prompt)
            logger.debug(f"Agent '{self.name}' invocation successful.")
            return result
        except Exception as e:
            logger.error(f"Error invoking agent '{self.name}': {e}")
            raise
