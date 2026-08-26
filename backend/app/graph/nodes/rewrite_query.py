from typing import Dict, Any
from app.services.bedrock_client import bedrock_service

def rewrite_query_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node that reformulates the user query when document grading fails,
    improving vector retrieval performance and incrementing the retry accumulator.
    
    Returns:
        Dict[str, Any]: State update containing 'rewritten_query' and incremented 'retries'.
    """
    query = state.get("query", "")
    current_retries = state.get("retries", 0)

    prompt = f"""You are a query rewrite optimizer for a GitHub trending repository retrieval engine.
The initial vector search for the user query produced weak or irrelevant results.
Reformulate the user query to make it clearer, more descriptive, and better suited for semantic vector retrieval.

Initial Query: "{query}"

Output ONLY the optimized query string without any preamble or explanation:"""

    try:
        rewritten = bedrock_service.generate(prompt=prompt, max_tokens=100, temperature=0.5).strip()
        # Clean quotes if present
        rewritten = rewritten.strip('"').strip("'")
    except Exception as e:
        print(f"[Rewrite Query Fallback] Error rewriting query: {e}")
        rewritten = f"GitHub trending repositories matching {query}"

    print(f"[Rewrite Query] Retry Attempt #{current_retries + 1} | Original: '{query}' -> Rewritten: '{rewritten}'")

    return {
        "rewritten_query": rewritten,
        "retries": 1  # Adds +1 to state retries accumulator
    }
