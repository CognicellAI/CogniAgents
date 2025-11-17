from pydantic import BaseModel, Field

class SupportRouteOutput(BaseModel):
    """
    Represents the routing decision for a customer support query.
    """
    department: str = Field(description="The department to route the query to (e.g., Technical Support, Billing, Sales, General Inquiry).")
    reason: str = Field(description="A brief explanation for the routing decision.")
