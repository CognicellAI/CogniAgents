import pytest
from pydantic import BaseModel

from cogni_agents.schemas import get_schema, SummaryOutput, SentimentOutput
from examples.customer_support_router.custom_schemas import SupportRouteOutput


def test_get_built_in_schemas(mocker):
    """Tests retrieving built-in schemas by name without loading config."""
    # Patch _load_custom_schemas to prevent file access, isolating the test.
    mocker.patch("cogni_agents.schemas._load_custom_schemas")

    assert get_schema("summary") == SummaryOutput
    assert get_schema("sentiment") == SentimentOutput
    assert get_schema("str") == str


def test_get_nonexistent_schema(mocker):
    """Tests that getting a non-existent schema raises a KeyError without loading config."""
    # Patch _load_custom_schemas to prevent file access, isolating the test.
    mocker.patch("cogni_agents.schemas._load_custom_schemas")

    with pytest.raises(KeyError, match="Schema 'nonexistent_schema' not found"):
        get_schema("nonexistent_schema")


def test_get_custom_schema(mock_test_config):
    """Tests loading and retrieving a custom schema defined in the config."""
    # The mock_test_config fixture handles loading the test config,
    # which now includes a custom schema definition.
    schema = get_schema("support_route_schema")

    assert issubclass(schema, BaseModel)
    assert schema == SupportRouteOutput
    assert "department" in schema.model_fields
    assert "reason" in schema.model_fields
