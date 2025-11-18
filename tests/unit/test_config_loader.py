from cogni_agents.config_loader import (
    get_agent_configs,
    get_workflow_configs,
    get_prompt_components,
    get_global_llm_settings,
)

def test_load_and_get_config_components(mock_test_config):
    """
    Tests that config components are loaded and retrieved correctly
    using the mock_test_config fixture.
    """
    # Test agent configs
    agents = get_agent_configs()
    assert isinstance(agents, list)
    assert len(agents) == 3
    assert agents[0]["name"] == "summarizer_agent"
    assert agents[1]["llm"]["temperature"] == 0.0 # Test override

    # Test workflow configs
    workflows = get_workflow_configs()
    assert isinstance(workflows, list)
    assert len(workflows) == 1
    assert workflows[0]["name"] == "test_analysis_workflow"

    # Test prompt components
    components = get_prompt_components()
    assert isinstance(components, dict)
    assert components["politeness"] == "Be polite."

    # Test global LLM settings
    llm_settings = get_global_llm_settings()
    assert isinstance(llm_settings, dict)
    assert llm_settings["model"] == "test-model"
