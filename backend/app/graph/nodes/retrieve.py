from typing import Dict, Any
from app.services.embeddings import embedding_service
from app.services.qdrant_client import qdrant_service

def retrieve_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node that retrieves relevant repo document chunks from Qdrant vector DB
    using the query or rewritten_query.
    """
    # Use rewritten query if available, otherwise original query
    query = state.get("rewritten_query") or state.get("query", "")
    
    # Generate vector embedding for the query string
    query_vector = embedding_service.embed_text(query)
    
    # Execute vector similarity search against Qdrant
    documents = qdrant_service.search_similar(query_vector=query_vector, top_k=5)
    
    return {
        "documents": documents or []
    }
