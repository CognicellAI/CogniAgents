from pydantic import BaseModel, Field

class WeatherReport(BaseModel):
    """Represents a weather report for a specific location."""
    location: str = Field(description="The city for the weather report.")
    temperature: int = Field(description="The temperature in Celsius.")
    forecast: str = Field(description="A brief description of the weather conditions.")
