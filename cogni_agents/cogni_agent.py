import logging
import os
from typing import Any, Dict, Type, Optional

from pydantic_ai import Agent as PydanticAIAgent
from pydantic_ai.models.openai import OpenAIChatModel

from .config_loader import get_global_llm_settings
from .schemas import OUTPUT_SCHEMAS

logger = logging.getLogger(__name__)

class CogniAgent:
    """
    A wrapper around PydanticAIAgent that handles configuration-driven agent creation.
    It maps config entries to PydanticAI agent parameters, including dynamic output types.
    """
    def __init__(self, agent_config: Dict[str, Any]):
        self.name = agent_config["name"]
        self.title = agent_config.get("title", self.name)
        self.description = agent_config.get("description")
        self.prompt = agent_config["prompt"]
        self.llm_model = agent_config["llm_model"]
        self.temperature = agent_config.get("temperature")
        self.output_schema_name = agent_config.get("output_schema")

        global_llm_settings = get_global_llm_settings()

        # Determine the LLM model to use, prioritizing agent-specific over global
        model_name = self.llm_model or global_llm_settings.get("model")
        if model_name is None:
            raise ValueError(f"Agent '{self.name}' missing LLM model name. "
                             "Specify 'llm_model' in agent config or 'global_llm_settings.model'.")

        # Resolve the output type from the OUTPUT_SCHEMAS registry
        self.output_type: Type[Any] = OUTPUT_SCHEMAS.get(
            self.output_schema_name, str
        )

        # Determine temperature, prioritizing agent-specific over global default
        temp = (
            self.temperature
            if self.temperature is not None
            else global_llm_settings.get("temperature", 0.1)
        )

        # Initialize OpenAIChatModel. The model name is passed via model_settings to PydanticAIAgent.
        # OpenAIChatModel itself does not take a 'model' argument in its constructor.
        chat_model = OpenAIChatModel()

        self.agent = PydanticAIAgent(
            chat_model,
            instructions=self._build_instructions(),
            output_type=self.output_type,
            model_settings={"temperature": temp, "model": model_name}, # Pass model name here
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

    async def invoke(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Invokes the underlying PydanticAI agent with the given input.

        Args:
            input_text: The primary input string for the agent.
            context: An optional dictionary containing additional context for the agent.
                     Currently not directly used by PydanticAIAgent.run, but can be
                     used for future prompt enrichment or tool invocation.

        Returns:
            The structured output from the agent, or a string if no schema is defined.
        """
        logger.debug(f"Invoking agent '{self.name}' with input: {input_text[:100]}...")
        try:
            result = await self.agent.run(input_text)
            logger.debug(f"Agent '{self.name}' invocation successful.")
            return result.output
        except Exception as e:
            logger.error(f"Error invoking agent '{self.name}': {e}")
            raise
