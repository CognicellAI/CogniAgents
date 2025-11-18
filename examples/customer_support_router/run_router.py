import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from cogni_agents.workflow_engine import run_workflow, render_workflow_output
from cogni_agents.config_loader import set_config_path

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Define the path to the configuration file for this example
CONFIG_FILE_NAME = "config.yaml"
CONFIG_FILE_PATH = Path(__file__).resolve().parent / CONFIG_FILE_NAME

# Set the configuration path for the CogniAgents library.
# This will automatically trigger a reload of all framework components.
set_config_path(str(CONFIG_FILE_PATH))
logger.info(f"Using configuration from: {CONFIG_FILE_PATH}")

CUSTOMER_QUERIES = [
    "My internet is not working, and I can't connect to any websites.",
    "I received a bill that seems much higher than usual. Can you check it?",
    "I'm interested in upgrading my current service plan to include faster speeds.",
    "I have a general question about your operating hours.",
    "The new software update broke my printer connection.",
    "I want to know if there are any promotions for existing customers.",
    "My payment didn't go through, and I need to update my card details.",
    "How do I reset my password for the online portal?",
]

async def main():
    """
    Runs the customer support routing workflow for several example queries.
    """
    workflow_name = "route_customer_query"

    print("\n" + "="*70)
    print("   CUSTOMER SUPPORT ROUTER SHOWCASE")
    print("="*70 + "\n")

    for i, query in enumerate(CUSTOMER_QUERIES):
        payload = {"customer_query": query}
        logger.info(f"\n--- Processing Query {i+1} ---")
        logger.info(f"Customer Query: '{query}'")

        try:
            # 1. Run the workflow to get the structured results
            context = await run_workflow(workflow_name, payload)

            # 2. Render the final output using the Jinja2 template
            final_output = render_workflow_output(workflow_name, context)

            # 3. Print the formatted report
            print(final_output)
            print("\n" + "-"*70 + "\n")

        except Exception as e:
            logger.error(f"An error occurred during the workflow execution for query '{query}': {e}", exc_info=True)
            print("\n---")
            print("Workflow execution failed. Please check the logs and ensure your .env file is set up correctly.")
            print("You need a running LLM service (e.g., OpenWebUI) and your API key configured.")
            print("Ensure your .env file in the project root has:")
            print("  OPENAI_BASE_URL=\"http://your-llm-endpoint:port/v1\"")
            print("  OPENAI_API_KEY=\"your-api-key\"")
            print("---")

if __name__ == '__main__':
    asyncio.run(main())
