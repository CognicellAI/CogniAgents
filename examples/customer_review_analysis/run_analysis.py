import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
# This assumes the script is in `examples/customer_review_analysis/`
# and the project root is two levels up.
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from cogni_agents.workflow_engine import run_workflow, render_workflow_output
from cogni_agents.config_loader import set_config_path, reload_config

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Define the path to the configuration file for this example
CONFIG_FILE_NAME = "customer_review_config.yaml"
CONFIG_FILE_PATH = Path(__file__).resolve().parent / CONFIG_FILE_NAME

# Set the configuration path for the CogniAgents library
set_config_path(str(CONFIG_FILE_PATH))
# Reload config to ensure the new path is used and agents/workflows are loaded
reload_config()
logger.info(f"Using configuration from: {CONFIG_FILE_PATH}")

CUSTOMER_REVIEW = """
I've been using the new SuperWidget 3000 for about two weeks now, and I have mixed feelings.
On one hand, the battery life is absolutely incredible. I can go for days without needing to charge it,
which is a huge improvement over my last device. The screen is also bright and vibrant.

However, the software feels a bit sluggish. There's a noticeable delay when switching between apps,
and it has crashed on me a couple of times. I also found the user interface to be a bit confusing
at first, though I'm getting used to it. Overall, it's a decent product with some great hardware,
but the software experience really needs some polish.
"""

async def main():
    """
    Runs the customer review analysis workflow and prints the output.
    """
    workflow_name = "analyze_customer_review"
    payload = {"review_text": CUSTOMER_REVIEW}

    logger.info(f"Starting workflow: '{workflow_name}'...")
    try:
        # 1. Run the workflow to get the structured results
        context = await run_workflow(workflow_name, payload)

        # 2. Render the final output using the Jinja2 template
        final_output = render_workflow_output(workflow_name, context)

        # 3. Print the formatted report
        print("\n" + "="*50)
        print("   CUSTOMER REVIEW ANALYSIS SHOWCASE")
        print("="*50 + "\n")
        print(final_output)
        print("\n" + "="*50)

    except Exception as e:
        logger.error(f"An error occurred during the workflow execution: {e}", exc_info=True)
        print("\n---")
        print("Workflow execution failed. Please check the logs and ensure your .env file is set up correctly.")
        print("You need a running LLM service (e.g., OpenWebUI) and your API key configured.")
        print("Ensure your .env file in the project root has:")
        print("  OPENAI_BASE_URL=\"http://your-llm-endpoint:port/v1\"")
        print("  OPENAI_API_KEY=\"your-api-key\"")
        print("---")

if __name__ == '__main__':
    # Ensure .env is loaded (handled by cogni_agents.config_loader)
    asyncio.run(main())
