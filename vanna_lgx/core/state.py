# vanna_lgx/core/state.py - S5 VERSION

from typing import TypedDict, List, Dict
import pandas as pd

class GraphState(TypedDict):
    """
    Represents the state of our graph for Stage S5.
    """
    # Input
    question: str
    rewritten_question: str      # <-- NEW: For the refined question
    
    # Context
    db_schema: str
    retrieved_examples: List[str]
    retrieved_docs: List[str]
    clean_context: Dict
    
    # SQL
    sql_query: str
    validation_error: str | None
    repair_attempts: int
    
    # Output
    result: pd.DataFrame | None
    summary: str
    visualization_spec: Dict | None # <-- NEW: To hold Vega-Lite JSON
    error: str | None