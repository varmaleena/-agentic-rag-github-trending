from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator

class AgentState(TypedDict):
    """
    Typed dictionary representing the shared state across LangGraph node transitions.
    Includes accumulator reducers for loop iteration tracking.
    """
    query: str
    rewritten_query: Optional[str]
    documents: List[Dict[str, Any]]
    relevance_grade: str  # "yes" or "no"
    answer: str
    eval_score: float
    retries: Annotated[int, operator.add]  # Accumulator pattern to safely count retries across loop iterations
    graph_path: List[str]  # Log of graph nodes executed for dashboard tracking
