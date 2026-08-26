from typing import Dict, Any
from app.services.bedrock_client import bedrock_service

def route_query_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node that analyzes the incoming user query and determines whether
    retrieval from the Qdrant vector database is required, or if the query can be
    answered directly (e.g. general greeting/chitchat).
    """
    query = state.get("query", "")
    
    prompt = f"""You are a routing classifier for a GitHub Trending Repository assistant.
Analyze the user query below and decide if it requires searching the repository database or if it can be answered directly without vector database retrieval.

Query: "{query}"

Respond with ONLY one word:
- "retrieve" if the query asks about repositories, code, stars, trending projects, technical documentation, or GitHub.
- "generate_direct" if the query is a general greeting, farewell, or non-technical chitchat.

Decision:"""

    decision = bedrock_service.generate(prompt=prompt, max_tokens=10, temperature=0.0).strip().lower()
    
    # Fallback default to retrieve if unclear
    route_decision = "retrieve" if "retrieve" in decision else "generate_direct"
    
    return {
        "relevance_grade": route_decision
    }
