import pytest
from cogni_agents.schemas import get_schema, SummaryOutput, SentimentOutput

def test_get_built_in_schemas():
    """Tests retrieving built-in schemas by name."""
    assert get_schema("summary") == SummaryOutput
    assert get_schema("sentiment") == SentimentOutput
    assert get_schema("str") == str

def test_get_nonexistent_schema():
    """Tests that getting a non-existent schema raises a KeyError."""
    with pytest.raises(KeyError, match="Schema 'nonexistent_schema' not found"):
        get_schema("nonexistent_schema")
