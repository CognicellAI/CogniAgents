import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to sys.path to allow absolute imports from cogni_agents
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from cogni_agents.config_loader import set_config_path
from cogni_agents.workflow_engine import render_workflow_output, run_workflow

# Set up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define the path to the configuration file for this example
CONFIG_FILE_NAME = "config.yaml"
CONFIG_FILE_PATH = Path(__file__).resolve().parent / CONFIG_FILE_NAME

# The customer review to be analyzed
CUSTOMER_REVIEW = """
I've been using the new SuperWidget 3000 for about two weeks now, and I have mixed feelings.
On one hand, the battery life is absolutely incredible. I can go for days without needing to charge,
which is a huge improvement over my last device. The screen is also bright and vibrant.

However, the software feels a bit sluggish. There's a noticeable delay when switching between apps,
and it has crashed on me a couple of times. I also found the user interface to be a bit confusing
at first, though I'm getting used to it. Overall, it's a decent product with some great hardware,
but the software experience really needs some polish.
"""


async def main():
    """
    Runs the 'analyze_customer_review' workflow with a sample customer review.
    """
    logger.info("Setting config path to: %s", CONFIG_FILE_PATH)
    set_config_path(str(CONFIG_FILE_PATH))

    workflow_name = "analyze_customer_review"
    payload = {"customer_review": CUSTOMER_REVIEW}

    logger.info("Running workflow '%s' with payload:", workflow_name)
    print(json.dumps(payload, indent=2))
    print("-" * 20)

    try:
        # Run the workflow and get the final context
        final_context = await run_workflow(workflow_name, payload)

        # Render the final output using the workflow's template
        output = render_workflow_output(workflow_name, final_context)

        print("\n" + "=" * 20 + " WORKFLOW OUTPUT " + "=" * 20)
        print(output)
        print("=" * 57)

    except Exception as e:
        logger.error(
            "An error occurred during workflow execution: %s", e, exc_info=True
        )


if __name__ == "__main__":
    # This allows the script to be run directly from the command line:
    # python examples/customer_review_analysis/run_analysis.py
    asyncio.run(main())
