# Guide: Using Agents with External Orchestrators (LangGraph)

A core design principle of CogniAgents is that agents are portable "tools." While the built-in workflow engine is great for simple, linear tasks, you are never locked into it. You can easily use your declaratively-defined agents in more powerful, external orchestration engines like [LangGraph](https://langchain-ai.github.io/langgraph/).

This guide demonstrates how to re-implement the "Customer Support Router" example using LangGraph, showcasing how `CogniAgent`s can serve as nodes in a complex graph.

### Prerequisites

You'll need to install LangGraph for this example.

```bash
pip install langgraph httpx-sse
```

---

## The LangGraph Implementation

Instead of defining the orchestration logic in YAML, we'll write a Python script that uses LangGraph to build a state machine, or "graph." The agents defined in `config.yaml` will serve as the tools that each node in the graph can call.

Below is the complete script, which you could save as `examples/customer_support_router/run_with_langgraph.py`.

```python
import asyncio
from pathlib import Path
from typing import TypedDict, Annotated

from langgraph.graph import StateGraph, END

from cogni_agents.agent_registry import ensure_agents_loaded, get_agent
from cogni_agents.config_loader import set_config_path

# Define the path to the configuration file
CONFIG_FILE_PATH = Path(__file__).resolve().parent / "config.yaml"

# --- 1. Define the State for the Graph ---
# This TypedDict represents the shared state that flows through the graph.
# Each node will read from and write to this state.
class GraphState(TypedDict):
    customer_query: str
    routing_decision: Annotated[dict, lambda x, y: {**x, **y}]
    final_response: str

# --- 2. Define the Nodes for the Graph ---
# Each node is an async function that takes the current state and returns a
# dictionary with the state updates.

async def route_query_node(state: GraphState):
    """Invokes the support_router agent to classify the query."""
    print("---NODE: route_query_node---")
    router_agent = get_agent("support_router")
    result = await router_agent.invoke({"customer_query": state["customer_query"]})
    return {"routing_decision": result}

async def technical_support_node(state: GraphState):
    """Invokes the technical_support_agent to generate a response."""
    print("---NODE: technical_support_node---")
    support_agent = get_agent("technical_support_agent")
    result = await support_agent.invoke({"customer_query": state["customer_query"]})
    return {"final_response": result}

async def billing_node(state: GraphState):
    """Invokes the billing_agent to generate a response."""
    print("---NODE: billing_node---")
    billing_agent = get_agent("billing_agent")
    result = await billing_agent.invoke({"customer_query": state["customer_query"]})
    return {"final_response": result}

async def sales_node(state: GraphState):
    """Invokes the sales_agent to generate a response."""
    print("---NODE: sales_node---")
    sales_agent = get_agent("sales_agent")
    result = await sales_agent.invoke({"customer_query": state["customer_query"]})
    return {"final_response": result}

async def general_inquiry_node(state: GraphState):
    """Invokes the general_inquiry_agent to generate a response."""
    print("---NODE: general_inquiry_node---")
    general_agent = get_agent("general_inquiry_agent")
    result = await general_agent.invoke({"customer_query": state["customer_query"]})
    return {"final_response": result}

# --- 3. Define the Conditional Edges ---
# This function inspects the state to decide which node to execute next.
def decide_next_node(state: GraphState):
    """Determines the next node based on the routing decision."""
    print("---EDGE: decide_next_node---")
    department = state["routing_decision"].department
    if department == "Technical Support":
        return "technical_support"
    elif department == "Billing":
        return "billing"
    elif department == "Sales":
        return "sales"
    else:
        return "general_inquiry"

# --- 4. Assemble the Graph ---
async def build_graph():
    """Builds and compiles the LangGraph state machine."""
    # First, ensure all agents from the config are loaded into memory.
    set_config_path(str(CONFIG_FILE_PATH))
    await ensure_agents_loaded()

    workflow = StateGraph(GraphState)

    # Add all the nodes
    workflow.add_node("router", route_query_node)
    workflow.add_node("technical_support", technical_support_node)
    workflow.add_node("billing", billing_node)
    workflow.add_node("sales", sales_node)
    workflow.add_node("general_inquiry", general_inquiry_node)

    # Define the graph's flow
    workflow.set_entry_point("router")
    workflow.add_conditional_edges(
        "router",
        decide_next_node,
        {
            "technical_support": "technical_support",
            "billing": "billing",
            "sales": "sales",
            "general_inquiry": "general_inquiry",
        },
    )

    # All responder nodes lead to the end
    workflow.add_edge("technical_support", END)
    workflow.add_edge("billing", END)
    workflow.add_edge("sales", END)
    workflow.add_edge("general_inquiry", END)

    # Compile the graph into a runnable object
    return workflow.compile()

# --- 5. Run the Graph ---
async def main():
    """Main function to run the LangGraph workflow."""
    graph = await build_graph()

    # Define the input payload
    customer_query = "My internet is not working, and I can't connect to any websites."
    initial_payload = {"customer_query": customer_query}

    # Invoke the graph and stream the results
    print(f"Running graph for query: '{customer_query}'\n")
    final_state = None
    async for event in graph.astream(initial_payload):
        for key, value in event.items():
            print(f"---STREAM EVENT---\nNode: {key}\nOutput: {value}\n")
            if key != "__end__":
                final_state = value

    print("\n---FINAL STATE---")
    print(f"Query: {final_state['customer_query']}")
    print(f"Routing: {final_state['routing_decision']}")
    print(f"Response: {final_state['final_response']}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Breaking Down the Script

1.  **State Definition (`GraphState`)**: This `TypedDict` defines the "memory" of our graph. It holds the initial query, the routing decision from the first agent, and the final response from the second agent.

2.  **Agent Nodes**: Each `async` function (e.g., `route_query_node`, `technical_support_node`) represents a node in our graph. Its logic is simple:
    -   Get a pre-configured agent using `get_agent("agent_name")`.
    -   Invoke the agent with data from the current `state`.
    -   Return a dictionary containing the data to update the state with.

3.  **Conditional Routing (`decide_next_node`)**: This function acts as a conditional edge. After the `router` node runs, LangGraph calls this function. It inspects the `department` in the state and returns the name of the *next* node to execute. This is how we achieve the same `when` logic as the built-in workflow engine.

4.  **Graph Assembly (`build_graph`)**: This is where we wire everything together.
    -   We initialize a `StateGraph` with our `GraphState`.
    -   We add each of our functions as a named node.
    -   We set the `entry_point` to tell the graph where to start.
    -   We use `add_conditional_edges` to connect the `router` to the decision function (`decide_next_node`) and map its string outputs to the actual nodes.
    -   Finally, we connect all the "responder" nodes to `END`, signifying that the workflow is complete after they run.

## Running the Graph

To run this implementation, you execute the Python script directly:

```bash
python examples/customer_support_router/run_with_langgraph.py
```

You will see a stream of events as the graph executes, first running the router, then the decision edge, and finally the selected support agent. The final output will show the complete state, containing the query, the routing decision, and the generated response.

This approach demonstrates the portability of `CogniAgent`s. You define their behavior once in YAML, and you can then use them as tools in any orchestration engine you choose, from the simple built-in engine to a powerful graph-based framework like LangGraph.
