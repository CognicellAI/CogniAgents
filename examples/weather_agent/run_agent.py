import asyncio
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'examples'))

from cogni_agents.cogni_agent import CogniAgent
from cogni_agents.config_loader import set_config_path

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Define the path to the configuration file for this example
CONFIG_FILE_NAME = "config.yaml"
CONFIG_FILE_PATH = Path(__file__).resolve().parent / CONFIG_FILE_NAME

# Set the configuration path for the CogniAgents library.
# This will automatically trigger a reload of all framework components.
set_config_path(str(CONFIG_FILE_PATH))
logger.info(f"Using configuration from: {CONFIG_FILE_PATH}")

async def main():
    """
    Runs the weather agent for a specific location.
    """
    agent_name = "weather_agent"
    location = "San Francisco"

    print("\n" + "="*70)
    print("   WEATHER AGENT SHOWCASE")
    print("="*70 + "\n")

    logger.info(f"Running agent '{agent_name}' for location: {location}")

    try:
        # 1. Initialize the agent
        agent = await CogniAgent.from_name(agent_name)

        # 2. Invoke the agent with the location
        result = await agent.invoke({"location": location})

        # 3. Print the result
        print("\nStructured Weather Report:")
        print(f"  - Location: {result.output.location}")
        print(f"  - Temperature: {result.output.temperature}°C")
        print(f"  - Forecast: {result.output.forecast}")

    except Exception as e:
        logger.error(f"An error occurred during the agent execution for location '{location}': {e}", exc_info=True)
        print("\n---")
        print("Agent execution failed. Please check the logs and ensure your .env file is set up correctly.")
        print("You need a running LLM service (e.g., OpenWebUI) and your API key configured.")
        print("Ensure your .env file in the project root has:")
        print("  OPENAI_BASE_URL=\"http://your-llm-endpoint:port/v1\"")
        print("  OPENAI_API_KEY=\"your-api-key\"")
        print("---")

if __name__ == '__main__':
    asyncio.run(main())
