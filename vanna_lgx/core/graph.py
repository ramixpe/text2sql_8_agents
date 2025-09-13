# vanna_lgx/core/graph.py - S2 VERSION

from langgraph.graph import StateGraph, END
from .state import GraphState
from .nodes import retrieve_context, synthesize_sql, execute_sql, summarize_result

def build_s2_graph():
    """Builds the StateGraph for Stage S2."""
    workflow = StateGraph(GraphState)

    # Add the nodes to the graph
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("synthesize_sql", synthesize_sql)
    workflow.add_node("execute_sql", execute_sql)
    workflow.add_node("summarize_result", summarize_result)

    # Define the edges for the S2 flow
    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "synthesize_sql")
    workflow.add_edge("synthesize_sql", "execute_sql")
    workflow.add_edge("execute_sql", "summarize_result")
    workflow.add_edge("summarize_result", END)

    # Compile the graph into a runnable app
    app = workflow.compile()
    return app