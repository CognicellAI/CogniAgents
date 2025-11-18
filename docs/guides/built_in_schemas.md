# Reference: Built-in Schemas

The CogniAgents framework includes several pre-defined schemas for common AI tasks. You can use these in your agent definitions by referencing their short names in the `output_schema` field, without needing to define a custom schema.

---

## `str`

The most basic output type, representing a single, unstructured string of text.

-   **Name in config**: `str`
-   **Use Case**: Ideal for agents that generate freeform text, like creative writing, drafting an email, or providing a simple answer.
-   **Output Type**: `string`
-   **Example Agent Config**:
    ```yaml
    agents:
      - name: simple_responder
        prompt: "Answer the user's question concisely. Question: {question}"
        output_schema: "str"
    ```

---

## `summary`

A structured schema for summarizing text, specifically designed to separate positive and negative aspects.

-   **Name in config**: `summary`
-   **Use Case**: Perfect for analyzing product reviews, user feedback, or any text where you need to extract pros and cons.
-   **Schema Definition**:
    ```python
    class SummaryOutput(BaseModel):
        positive_aspects: List[str]
        negative_aspects: List[str]
    ```
-   **Example Agent Config**:
    ```yaml
    agents:
      - name: review_summarizer
        prompt: "Summarize the key positive and negative points from this review: {review_text}"
        output_schema: "summary"
    ```

---

## `sentiment`

A structured schema for sentiment analysis.

-   **Name in config**: `sentiment`
-   **Use Case**: Classifying a piece of text as positive, negative, or neutral, and requiring the agent to provide a justification for its decision.
-   **Schema Definition**:
    ```python
    class SentimentOutput(BaseModel):
        sentiment: str  # e.g., "positive", "neutral", "negative"
        rationale: str  # A short explanation for the sentiment
    ```
-   **Example Agent Config**:
    ```yaml
    agents:
      - name: sentiment_analyzer
        prompt: "Analyze the sentiment of this comment: {comment_text}"
        output_schema: "sentiment"
    ```

---

## `code_review`

A structured schema for performing a high-level automated code review.

-   **Name in config**: `code_review`
-   **Use Case**: Analyzing a code snippet to identify potential issues, suggest improvements, and assess the overall risk level. This is useful for automated quality checks.
-   **Schema Definition**:
    ```python
    class CodeReviewOutput(BaseModel):
        issues: List[str]
        suggestions: List[str]
        risk_level: str # e.g., "low", "medium", "high"
    ```
-   **Example Agent Config**:
    ```yaml
    agents:
      - name: basic_code_reviewer
        prompt: "Review the following code for issues and suggest improvements: {code_snippet}"
        output_schema: "code_review"
    ```
