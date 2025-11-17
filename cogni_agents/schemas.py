from typing import Type, Dict, Union, List
from pydantic import BaseModel, Field


class SummaryOutput(BaseModel):
    """
    Represents a summarized text output, specifically for customer reviews.
    """
    positive_aspects: List[str] = Field(default_factory=list, description="List of positive points identified in the review.")
    negative_aspects: List[str] = Field(default_factory=list, description="List of negative points identified in the review.")


class SentimentOutput(BaseModel):
    """
    Represents the sentiment analysis of a text.
    """
    sentiment: str = Field(description="The overall sentiment (e.g., positive, neutral, negative).")
    rationale: str = Field(description="A short explanation for the determined sentiment.")


class CodeReviewOutput(BaseModel):
    """
    Represents the output of a code review.
    """
    issues: List[str] = Field(default_factory=list, description="List of key issues found in the code.")
    suggestions: List[str] = Field(default_factory=list, description="List of suggested improvements for the code.")
    risk_level: str = Field(description="The overall risk level of the code (e.g., low, medium, high).")


# Map logical schema names to actual Python types (Pydantic models or str)
OUTPUT_SCHEMAS: Dict[str, Type[BaseModel] | Type[str]] = {
    "summary": SummaryOutput,
    "sentiment": SentimentOutput,
    "code_review": CodeReviewOutput,
    # Default to str if a schema name is not found here
}
