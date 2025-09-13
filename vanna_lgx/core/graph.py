# vanna_lgx/core/graph.py - S5 FINAL VERSION

from langgraph.graph import StateGraph, END
from .state import GraphState
from .nodes import (
    query_rewriter,
    retrieve_context, 
    rerank_and_judge, 
    synthesize_sql, 
    sql_linter_verifier, 
    auto_repair, 
    execute_sql, 
    summarize_and_visualize,
    MAX_REPAIR_ATTEMPTS
)

def should_continue(state: GraphState) -> str:
    """ The logic for the repair loop conditional edge. """
    if error := state.get("validation_error"):
        if state.get("repair_attempts", 0) < MAX_REPAIR_ATTEMPTS:
            return "repair"
        else:
            return "end_with_error"
    else:
        return "execute"

def build_s5_graph():
    """Builds the final StateGraph for Stage S5."""
    workflow = StateGraph(GraphState)

    # Add all nodes for the final agent
    workflow.add_node("query_rewriter", query_rewriter)
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("rerank_and_judge", rerank_and_judge)
    workflow.add_node("synthesize_sql", synthesize_sql)
    workflow.add_node("sql_linter_verifier", sql_linter_verifier)
    workflow.add_node("auto_repair", auto_repair)
    workflow.add_node("execute_sql", execute_sql)
    workflow.add_node("summarize_and_visualize", summarize_and_visualize)

    # Build the graph
    workflow.set_entry_point("query_rewriter")
    workflow.add_edge("query_rewriter", "retrieve_context")
    workflow.add_edge("retrieve_context", "rerank_and_judge")
    workflow.add_edge("rerank_and_judge", "synthesize_sql")
    workflow.add_edge("synthesize_sql", "sql_linter_verifier")
    
    workflow.add_conditional_edges(
        "sql_linter_verifier",
        should_continue,
        {
            "repair": "auto_repair",
            "execute": "execute_sql",
            "end_with_error": "summarize_and_visualize" # Route errors to final summary
        }
    )
    
    workflow.add_edge("auto_repair", "synthesize_sql")
    workflow.add_edge("execute_sql", "summarize_and_visualize")
    workflow.add_edge("summarize_and_visualize", END)

    app = workflow.compile()
    return app