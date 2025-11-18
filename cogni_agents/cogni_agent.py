import logging
from typing import Any, Dict, Type

from jinja2 import Environment
from pydantic_ai import Agent as PydanticAIAgent
from pydantic_ai.models.openai import OpenAIChatModel

from .config_loader import get_global_llm_settings, get_prompt_components
from .schemas import get_schema

logger = logging.getLogger(__name__)

class CogniAgent:
    """
    A wrapper around PydanticAIAgent that handles configuration-driven agent creation.
    It maps config entries to PydanticAI agent parameters, including dynamic output types.
    """
    def __init__(self, agent_config: Dict[str, Any]):
        self.name = agent_config["name"]
        self.description = agent_config.get("description")
        self.output_schema_name = agent_config.get("output_schema")

        # Render the prompt using Jinja2 to allow for composable prompt components
        raw_prompt = agent_config["prompt"]
        try:
            env = Environment()
            template = env.from_string(raw_prompt)
            self.prompt = template.render(prompt_components=get_prompt_components())
        except Exception as e:
            logger.error(f"Error rendering prompt for agent '{self.name}': {e}. Using raw prompt.")
            self.prompt = raw_prompt

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

        # Initialize the underlying PydanticAI components
        chat_model = OpenAIChatModel(model_name=model_name)

        # The remaining settings (temperature, etc.) are passed to the agent
        # The `llm` (chat_model) is passed as a positional argument, not a keyword argument.
        self.agent = PydanticAIAgent(
            chat_model,
            instructions=self._build_instructions(),
            output_type=self.output_type,
            model_settings=final_llm_settings,
        )

        logger.info(
            f"Initialized CogniAgent '{self.name}' with model='{model_name}', "
            f"output_type={self.output_type.__name__ if hasattr(self.output_type, '__name__') else str(self.output_type)}"
        )

    def _build_instructions(self) -> str:
        """
        Builds the instructions for the PydanticAI agent.
        This method can be extended to dynamically enrich the prompt with schema hints
        or other context based on the output_type.
        """
        # For now, it simply returns the configured prompt.
        # Future enhancement: Add schema introspection here.
        return self.prompt

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
        # The PydanticAIAgent.run method expects a single string input.
        # We need to format the prompt using the input_data.
        try:
            # Format the agent's base prompt with the provided input_data
            formatted_prompt = self.prompt.format(**input_data)
        except KeyError as e:
            logger.error(f"Missing key in input_data for agent '{self.name}' prompt: {e}. Input data: {input_data}")
            raise ValueError(f"Prompt formatting failed for agent '{self.name}'. Missing key: {e}")

        logger.debug(f"Invoking agent '{self.name}' with formatted prompt: {formatted_prompt[:200]}...")
        try:
            # Pass the *formatted_prompt* as the single input string to the PydanticAIAgent's run method
            result = await self.agent.run(formatted_prompt)
            logger.debug(f"Agent '{self.name}' invocation successful.")
            return result
        except Exception as e:
            logger.error(f"Error invoking agent '{self.name}': {e}")
            raise
