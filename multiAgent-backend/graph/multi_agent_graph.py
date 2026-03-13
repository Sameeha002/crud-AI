from langgraph.graph import StateGraph, START, END
from state import State
from memory import checkpointer
from agents.supervisor import run_supervisor
from agents.music_agent import run_music_agent
from agents.sales_agent import run_sales_agent

def route_to_agent(state: dict):
    """
    Reads next_agent from state and returns which node to go to.
    Called by add_conditional_edges after supervisor runs.
    """

    return state["next_agent"]

builder = StateGraph(State)

builder.add_node("supervisor", run_supervisor)
builder.add_node("music_agent", run_music_agent)
builder.add_node("sales_agent", run_sales_agent)

builder.add_edge(START, "supervisor")

builder.add_conditional_edges(
    "supervisor",
    route_to_agent,
    {
        "music_agent": "music_agent",
        "sales_agent": "sales_agent"
    }
)

builder.add_edge("music_agent", END)
builder.add_edge("sales_agent", END)

graph = builder.compile(checkpointer=checkpointer)

