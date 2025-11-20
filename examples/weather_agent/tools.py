import random

from typing import Dict, Any

def get_current_weather(location: str) -> Dict[str, Any]:
    """Gets the current weather for a given location."""
    if "tokyo" in location.lower():
        return {"location": "Tokyo", "temperature": 20, "forecast": "sunny"}
    elif "san francisco" in location.lower():
        return {"location": "San Francisco", "temperature": 15, "forecast": "foggy"}
    else:
        return {"location": location, "temperature": random.randint(10, 30), "forecast": "cloudy"}