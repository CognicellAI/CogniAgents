import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path to allow imports from cogni_agents
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from cogni_agents.workflow_engine import run_workflow, render_workflow_output
from cogni_agents.config_loader import reload_config

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- Example Customer Review ---
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
    # Set the config path to the example-specific config file
    config_path = Path(__file__).resolve().parent / "customer_review_config.yaml"
    os.environ["COGNIA_CONFIG_PATH"] = str(config_path)
    logger.info(f"Using configuration from: {config_path}")

    # Reload all modules to ensure they pick up the new config path
    reload_config()

    workflow_name = "analyze_customer_review"
    payload = {
        "review_text": CUSTOMER_REVIEW
    }

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
        print("You need a running OpenWebUI instance and the following in your .env file:")
        print("  OPENAI_BASE_URL=\"http://your-openwebui-url:8080/v1\"")
        print("  OPENAI_API_KEY=\"your-api-key\"")
        print("---")


if __name__ == "__main__":
    # Ensure you have a .env file in the project root with your OpenWebUI credentials
    # before running this script.
    if not (project_root / ".env").exists():
        print("ERROR: .env file not found in the project root.")
        print("Please create it with your OPENAI_BASE_URL and OPENAI_API_KEY.")
    else:
        asyncio.run(main())
