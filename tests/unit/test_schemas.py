import pytest
from pydantic import BaseModel
from unittest.mock import patch

from cogni_agents.schemas import get_schema, SummaryOutput, SentimentOutput
from pydantic import BaseModel, Field

# A mock schema for testing
class MockOutput(BaseModel):
    field1: str = Field(description="Field 1")
    field2: int = Field(description="Field 2")


def test_get_built_in_schemas():
    """Tests retrieving built-in schemas by name without loading config."""
    # Patch _load_custom_schemas to prevent file access, isolating the test.
    with patch("cogni_agents.schemas._load_custom_schemas"):
        assert get_schema("summary") == SummaryOutput
        assert get_schema("sentiment") == SentimentOutput
        assert get_schema("str") == str


def test_get_nonexistent_schema():
    """
    Tests that get_schema returns `str` for an unknown schema name,
    which is the expected fail-safe behavior.
    """
    # Patch _load_custom_schemas to prevent file access, isolating the test.
    with patch("cogni_agents.schemas._load_custom_schemas"):
        # The implementation safely defaults to `str` instead of raising an error.
        assert get_schema("nonexistent_schema") == str


def test_get_custom_schema(mock_test_config):
    """Tests loading and retrieving a custom schema defined in the config."""
    # The mock_test_config fixture handles loading the test config,
    # which now includes a custom schema definition.
    schema = get_schema("mock_schema")

    assert issubclass(schema, BaseModel)
    assert schema == MockOutput
    assert "field1" in schema.model_fields
    assert "field2" in schema.model_fields
