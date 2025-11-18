import importlib
import logging
from typing import Dict, List, Type

from pydantic import BaseModel, Field

from .config_loader import get_custom_schema_configs

logger = logging.getLogger(__name__)


# --- Built-in Schemas ---
# These serve as convenient defaults that users can use out of the box.

class SummaryOutput(BaseModel):
    """
    Represents a summarized text output, specifically for customer reviews.
    """
    summary: str = Field(description="A concise summary of the entire text.")
    positive_aspects: List[str] = Field(default_factory=list, description="List of positive points identified in the review.")
    negative_aspects: List[str] = Field(default_factory=list, description="List of negative points identified in the review.")


class SentimentOutput(BaseModel):
    """
    Represents the sentiment analysis of a text.
    """
    sentiment: str = Field(description="The overall sentiment (e.g., positive, neutral, negative).")
    rationale: str = Field(description="A short explanation for the determined sentiment.")


class CodeReviewOutput(BaseModel):
    """
    Represents the output of a code review.
    """
    issues: List[str] = Field(default_factory=list, description="List of key issues found in the code.")
    suggestions: List[str] = Field(default_factory=list, description="List of suggested improvements for the code.")
    risk_level: str = Field(description="The overall risk level of the code (e.g., low, medium, high).")


# --- Dynamic Schema Registry ---

# Start the registry with the built-in schemas and the primitive `str` type.
_schema_registry: Dict[str, Type[BaseModel] | Type[str]] = {
    "summary": SummaryOutput,
    "sentiment": SentimentOutput,
    "code_review": CodeReviewOutput,
    "str": str,
}

_custom_schemas_loaded = False


def _load_custom_schemas():
    """
    Dynamically imports and registers custom schemas from the config file.
    This function is idempotent, only loading schemas once per session unless reloaded.
    """
    global _custom_schemas_loaded
    if _custom_schemas_loaded:
        return

    logger.info("Loading custom schemas from configuration...")
    custom_schema_configs = get_custom_schema_configs()
    if not custom_schema_configs:
        logger.info("No custom schemas found in configuration.")
        _custom_schemas_loaded = True
        return

    for name, path in custom_schema_configs.items():
        if name in _schema_registry:
            logger.warning(f"Custom schema name '{name}' overrides a built-in schema.")
        try:
            module_path, class_name = path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            schema_class = getattr(module, class_name)
            _schema_registry[name] = schema_class
            logger.info(f"Successfully registered custom schema '{name}' from '{path}'.")
        except (ImportError, AttributeError, ValueError) as e:
            logger.error(f"Failed to load custom schema '{name}' from path '{path}': {e}")
            # For robustness, we log the error but don't halt the entire application.
            # The agent using this schema will fail later, which is more localized.

    _custom_schemas_loaded = True
    logger.info(f"Custom schema loading complete. Total schemas registered: {len(_schema_registry)}")


def get_schema(name: str | None) -> Type[BaseModel] | Type[str]:
    """
    Retrieves a schema by name from the registry, loading custom schemas if needed.

    Args:
        name: The logical name of the schema as defined in the config.

    Returns:
        The corresponding Pydantic model or `str` type. Defaults to `str` if the
        name is None or not found in the registry.
    """
    if not name:
        return str

    _load_custom_schemas()
    return _schema_registry.get(name, str)


def reload_schemas():
    """
    Forces a reload of custom schemas on the next `get_schema` call.
    This is typically called by `reload_config`.
    """
    global _custom_schemas_loaded
    logger.info("Marking custom schemas for reload.")
    _custom_schemas_loaded = False
