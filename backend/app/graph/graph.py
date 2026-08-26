from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes.route_query import route_query_node
from app.graph.nodes.retrieve import retrieve_node
from app.graph.nodes.grade_documents import grade_documents_node
from app.graph.nodes.rewrite_query import rewrite_query_node
from app.graph.nodes.generate import generate_node
from app.graph.nodes.evaluate import evaluate_node
from app.graph.nodes.flag_reindex import flag_reindex_node
from app.config import settings

def decide_to_route(state: AgentState) -> str:
    """
    Conditional edge function determining whether to retrieve documents or generate directly.
    """
    decision = state.get("relevance_grade", "retrieve")
    if decision == "generate_direct":
        return "generate"
    return "retrieve"

def decide_to_generate_or_rewrite(state: AgentState) -> str:
    """
    Conditional edge function determining whether to generate an answer or rewrite query and loop back.
    Enforces MAX_RETRIEVAL_RETRIES hard cap (default 3) to guarantee finite graph termination.
    """
    retries = state.get("retries", 0)
    relevance_grade = state.get("relevance_grade", "no")
    
    print(f"[Graph Router] Current retries: {retries}/{settings.MAX_RETRIEVAL_RETRIES} | Relevance Grade: {relevance_grade}")

    # Enforce termination cap: if retries >= MAX_RETRIEVAL_RETRIES or documents are graded relevant
    if retries >= settings.MAX_RETRIEVAL_RETRIES or relevance_grade == "yes":
        return "generate"
    
    return "rewrite_query"

def decide_eval_outcome(state: AgentState) -> str:
    """
    Conditional edge function determining whether to complete graph or flag low-scoring chunks.
    """
    eval_score = state.get("eval_score", 1.0)
    if eval_score < settings.EVAL_SCORE_THRESHOLD:
        return "flag_reindex"
    return "end"

def build_graph():
    """
    Assembles the StateGraph wiring all nodes and conditional edges for the Corrective RAG agent.
    """
    workflow = StateGraph(AgentState)
    
    # 1. Add all graph nodes
    workflow.add_node("route_query", route_query_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("grade_documents", grade_documents_node)
    workflow.add_node("rewrite_query", rewrite_query_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("flag_reindex", flag_reindex_node)
    
    # 2. Set Entry Point
    workflow.set_entry_point("route_query")
    
    # 3. Add Conditional Edge from route_query
    workflow.add_conditional_edges(
        "route_query",
        decide_to_route,
        {
            "retrieve": "retrieve",
            "generate": "generate"
        }
    )
    
    # 4. Connect retrieve to grade_documents
    workflow.add_edge("retrieve", "grade_documents")
    
    # 5. Add Conditional Edge from grade_documents (Loop or Generate)
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate_or_rewrite,
        {
            "generate": "generate",
            "rewrite_query": "rewrite_query"
        }
    )
    
    # 6. Connect rewrite_query back to retrieve (Corrective Loop)
    workflow.add_edge("rewrite_query", "retrieve")
    
    # 7. Connect generate to evaluate
    workflow.add_edge("generate", "evaluate")
    
    # 8. Add Conditional Edge from evaluate to END or flag_reindex
    workflow.add_conditional_edges(
        "evaluate",
        decide_eval_outcome,
        {
            "flag_reindex": "flag_reindex",
            "end": END
        }
    )
    
    # 9. Connect flag_reindex to END
    workflow.add_edge("flag_reindex", END)
    
    return workflow.compile()

# Global compiled graph instance
app_graph = build_graph()
