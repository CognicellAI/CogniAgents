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

def test_load_config_success(mock_test_config):
    """Test that _load_config successfully loads and caches the config."""
    config = _load_config()
    assert isinstance(config, dict)
    assert config["global_llm_settings"]["model"] == "gemini-2.5-flash"
    assert len(config["agents"]) == 3
    # Ensure it's cached
    with patch("builtins.open") as mock_open_again:
        _load_config()
        mock_open_again.assert_not_called() # Should not open file again


def test_load_config_file_not_found(monkeypatch):
    """Test that _load_config raises FileNotFoundError if config file is missing."""
    monkeypatch.setenv("COGNIA_CONFIG_PATH", "non_existent_file.yaml")
    reload_config() # Reload to use the new path
    with pytest.raises(FileNotFoundError, match="Configuration file not found at non_existent_file.yaml"):
        _load_config()


def test_load_config_yaml_error():
    """Test that _load_config raises ValueError for malformed YAML."""
    reload_config()
    with patch("builtins.open", mock_open(read_data="bad: yaml:")):
        with pytest.raises(ValueError, match="Error parsing YAML configuration"):
            _load_config()


def test_load_config_not_dict_at_root():
    """Test that _load_config raises ValueError if root is not a dictionary."""
    reload_config()
    with patch("builtins.open", mock_open(read_data="- item1\n- item2")):
        with pytest.raises(ValueError, match="Config file must contain a dictionary at its root."):
            _load_config()


def test_get_global_llm_settings(mock_test_config):
    """Test retrieving global LLM settings."""
    settings = get_global_llm_settings()
    assert settings == {"model": "gemini-2.5-flash", "temperature": 0.5}


def test_get_global_llm_settings_empty():
    """Test retrieving global LLM settings when not present."""
    reload_config()
    with patch("builtins.open", mock_open(read_data="agents: []")):
        settings = get_global_llm_settings()
        assert settings == {}


def test_get_agent_configs(mock_test_config):
    """Test retrieving agent configurations."""
    agents = get_agent_configs()
    assert len(agents) == 3
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


def test_get_workflow_configs(mock_test_config):
    """Test retrieving workflow configurations."""
    workflows = get_workflow_configs()
    assert len(workflows) == 4
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


def test_get_template_exists(mock_test_config):
    """Test retrieving an existing template."""
    template = get_template("test_workflow_1")
    assert template == "Summary: {{ results.step1_result.summary }}"


def test_get_template_not_exists(mock_test_config):
    """Test retrieving a non-existent template."""
    template = get_template("non_existent_workflow")
    assert template is None


def test_get_template_templates_not_dict():
    """Test retrieving template when templates section is not a dict."""
    reload_config()
    with patch("builtins.open", mock_open(read_data="templates: - item")):
        with pytest.raises(ValueError, match="Templates configuration must be a dictionary."):
            get_template("any_workflow")


def test_get_defaults(mock_test_config):
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


def test_reload_config(monkeypatch):
    """Test that reload_config clears the cache and reloads."""
    # Set initial config
    monkeypatch.setenv("COGNIA_CONFIG_PATH", "initial_config.yaml")
    with patch("builtins.open", mock_open(read_data="global_llm_settings: {model: 'initial'}")):
        reload_config()
        settings = get_global_llm_settings()
        assert settings["model"] == "initial"

    # Set new config path and reload
    monkeypatch.setenv("COGNIA_CONFIG_PATH", "reloaded_config.yaml")
    with patch("builtins.open", mock_open(read_data="global_llm_settings: {model: 'reloaded'}")):
        reload_config()
        settings = get_global_llm_settings()
        assert settings["model"] == "reloaded"
