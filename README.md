# Example Showcase: Customer Review Analysis

This example demonstrates how to use the CogniAgents framework to build a practical workflow that analyzes a customer review.

## What it Does

The `run_customer_review_analysis.py` script executes a workflow named `analyze_customer_review` defined in `customer_review_config.yaml`. This workflow performs two tasks in parallel:

1.  **Summarization**: An agent (`review_summarizer`) reads the customer review and extracts the key points.
2.  **Sentiment Analysis**: Another agent (`review_sentiment_analyzer`) determines the overall sentiment of the review and provides a rationale.

Finally, the script uses a Jinja2 template to render the results into a clean, human-readable report.

## How to Run

### 1. Prerequisites

- Ensure you have completed the setup instructions in the main `README.md` file, including installing dependencies (`pip install -e ".[dev]"`).
- Make sure you have a `.env` file in the **project root directory** with your OpenWebUI credentials (`OPENAI_BASE_URL` and `OPENAI_API_KEY`).
- Your OpenWebUI instance must be running and accessible.

### 2. Run the Script

From the **project root directory**, run the following command:

```bash
python examples/run_customer_review_analysis.py
```

### 3. Expected Output

If successful, you will see a formatted report printed to your console, similar to this:

```
==================================================
   CUSTOMER REVIEW ANALYSIS SHOWCASE
==================================================

# Customer Review Analysis Report
---
## Original Review:

I've been using the new SuperWidget 3000 for about two weeks now, and I have mixed feelings.
On one hand, the battery life is absolutely incredible. I can go for days without needing to charge it,
which is a huge improvement over my last device. The screen is also bright and vibrant.

However, the software feels a bit sluggish. There's a noticeable delay when switching between apps,
and it has crashed on me a couple of times. I also found the user interface to be a bit confusing
at first, though I'm getting used to it. Overall, it's a decent product with some great hardware,
but the software experience really needs some polish.

---
## Key Points (Summary):
- The battery life is exceptionally long.
- The screen is bright and vibrant.
- The software performance is sluggish with noticeable delays.
- The software has crashed multiple times.
- The user interface is initially confusing.
---
## Sentiment Analysis:
- **Sentiment:** Neutral
- **Rationale:** The review contains a mix of strong positive feedback (battery, screen) and significant negative feedback (sluggish software, crashes), making the overall sentiment neutral or mixed.

==================================================
```

*(Note: The exact summary and rationale will vary depending on the LLM you are using.)*

This example showcases the core power of the framework: defining agents and chaining them in a workflow, all driven by a simple YAML configuration file, to produce a structured and well-formatted result.
