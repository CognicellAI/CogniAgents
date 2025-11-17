# Guide: Using Agents with External Orchestrators (LangGraph)

A core design principle of CogniAgents is that agents are portable "tools." While the built-in workflow engine is great for simple, linear tasks, you are never locked into it. You can easily use your declaratively-defined agents in more powerful, external orchestration engines like [LangGraph](https://langchain-ai.github.io/langgraph/).

This guide demonstrates how to re-implement the "Customer Support Router" example using LangGraph, showcasing how `CogniAgent`s can serve as nodes in a complex graph.

### Prerequisites

You'll need to install LangGraph for this example. You can add it to your environment by installing the `langgraph` extra dependency:

