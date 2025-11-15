import pytest
import yaml
from unittest.mock import patch, mock_open
from cogni_agents.config_loader import (
    _load_config,
    get_global_llm_settings,
    get_agent_configs,
    get_workflow_configs,
    get_template,
    get_defaults,
    reload_config,
    CONFIG_FILE_PATH
)

# SAMPLE_CONFIG_CONTENT is now in conftest.py
# mock_config_file fixture is now handled by mock_config_content in conftest.py
# and reset_all_modules_state also handles reload_config()

def test_load_config_success(mock_config_content):
    """Test that _load_config successfully loads and caches the config."""
    config = _load_config()
    assert isinstance(config, dict)
    assert config["global_llm_settings"]["model"] == "test-model"
    assert len(config["agents"]) == 3 # Updated count due to conftest.py sample
    # Ensure it's cached
    with patch("builtins.open") as mock_open_again:
        _load_config()
        mock_open_again.assert_not_called() # Should not open file again


def test_load_config_file_not_found():
    """Test that _load_config raises FileNotFoundError if config file is missing."""
    # We need to ensure the config is not loaded from the default config.yaml
    # and that the mock_config_content fixture doesn't interfere.
    reload_config() # Clear any cached config
    with patch("builtins.open", side_effect=FileNotFoundError) as mock_file_open:
        with pytest.raises(FileNotFoundError, match=f"Configuration file not found at {CONFIG_FILE_PATH}"):
            _load_config()
        mock_file_open.assert_called_once_with(CONFIG_FILE_PATH, 'r')


def test_load_config_yaml_error():
    """Test that _load_config raises ValueError for malformed YAML."""
    reload_config() # Clear any cached config
    with patch("builtins.open", mock_open(read_data="invalid: - yaml")) as mock_file_open:
        with pytest.raises(ValueError, match="Error parsing YAML configuration"):
            _load_config()
        mock_file_open.assert_called_once_with(CONFIG_FILE_PATH, 'r')


def test_load_config_not_dict_at_root():
    """Test that _load_config raises ValueError if root is not a dictionary."""
    reload_config() # Clear any cached config
    with patch("builtins.open", mock_open(read_data="- item1\n- item2")) as mock_file_open:
        with pytest.raises(ValueError, match="Config file must contain a dictionary at its root."):
            _load_config()
        mock_file_open.assert_called_once_with(CONFIG_FILE_PATH, 'r')


def test_get_global_llm_settings(mock_config_content):
    """Test retrieving global LLM settings."""
    settings = get_global_llm_settings()
    assert settings == {"model": "test-model", "temperature": 0.5}


def test_get_global_llm_settings_empty():
    """Test retrieving global LLM settings when not present."""
    reload_config()
    with patch("builtins.open", mock_open(read_data="agents: []")):
        settings = get_global_llm_settings()
        assert settings == {}


def test_get_agent_configs(mock_config_content):
    """Test retrieving agent configurations."""
    agents = get_agent_configs()
    assert len(agents) == 3 # Updated count due to conftest.py sample
    assert agents[0]["name"] == "test_agent_1"
    assert agents[1]["llm_model"] == "model-2"


def test_get_agent_configs_empty():
    """Test retrieving agent configurations when not present."""
    reload_config()
    with patch("builtins.open", mock_open(read_data="global_llm_settings: {}")):
        agents = get_agent_configs()
        assert agents == []


def test_get_agent_configs_not_list():
    """Test retrieving agent configurations when it's not a list."""
    reload_config()
    with patch("builtins.open", mock_open(read_data="agents: {name: 'bad'}")):
        with pytest.raises(ValueError, match="Agents configuration must be a list."):
            get_agent_configs()


def test_get_workflow_configs(mock_config_content):
    """Test retrieving workflow configurations."""
    workflows = get_workflow_configs()
    assert len(workflows) == 4 # Updated count due to conftest.py sample
    assert workflows[0]["name"] == "test_workflow_1"
    assert workflows[1]["steps"][0]["input_from"] == "results.step1_result.summary"


def test_get_workflow_configs_empty():
    """Test retrieving workflow configurations when not present."""
    reload_config()
    with patch("builtins.open", mock_open(read_data="global_llm_settings: {}")):
        workflows = get_workflow_configs()
        assert workflows == []


def test_get_workflow_configs_not_list():
    """Test retrieving workflow configurations when it's not a list."""
    reload_config()
    with patch("builtins.open", mock_open(read_data="workflows: {name: 'bad'}")):
        with pytest.raises(ValueError, match="Workflows configuration must be a list."):
            get_workflow_configs()


def test_get_template_exists(mock_config_content):
    """Test retrieving an existing template."""
    template = get_template("test_workflow_1")
    assert template == "Summary: {{ results.step1_result.summary }}"


def test_get_template_not_exists(mock_config_content):
    """Test retrieving a non-existent template."""
    template = get_template("non_existent_workflow")
    assert template is None


def test_get_template_templates_not_dict():
    """Test retrieving template when templates section is not a dict."""
    reload_config()
    with patch("builtins.open", mock_open(read_data="templates: - item")):
        with pytest.raises(ValueError, match="Templates configuration must be a dictionary."):
            get_template("any_workflow")


def test_get_defaults(mock_config_content):
    """Test retrieving default settings."""
    defaults = get_defaults()
    assert defaults == {"max_tokens": 1024, "language": "en"}


def test_get_defaults_empty():
    """Test retrieving default settings when not present."""
    reload_config()
    with patch("builtins.open", mock_open(read_data="global_llm_settings: {}")):
        defaults = get_defaults()
        assert defaults == {}


def test_get_defaults_not_dict():
    """Test retrieving default settings when it's not a dict."""
    reload_config()
    with patch("builtins.open", mock_open(read_data="defaults: - item")):
        with pytest.raises(ValueError, match="Defaults configuration must be a dictionary."):
            get_defaults()


def test_reload_config(mock_config_content):
    """Test that reload_config clears the cache and reloads."""
    # Load config once
    _load_config()
    # Now, change the mock content and reload
    mock_config_content.side_effect = [mock_open(read_data="global_llm_settings: {model: 'reloaded-model'}").return_value]
    reload_config()
    # Ensure new config is loaded
    settings = get_global_llm_settings()
    assert settings["model"] == "reloaded-model"
    # The mock_open should have been called twice: once by initial _load_config, once by reload_config
    assert mock_config_content.call_count == 2
