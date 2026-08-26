import time
from typing import Dict, Any
from app.services.qdrant_client import qdrant_service

FLAGGED_CHUNKS_LOG = []

def flag_reindex_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node triggered when evaluation score is below threshold (< 0.7).
    Flags retrieved chunk IDs in Qdrant / flagged store for re-indexing or manual review.
    """
    eval_score = state.get("eval_score", 0.0)
    query = state.get("query", "")
    documents = state.get("documents", [])
    
    flagged_records = []
    for doc in documents:
        chunk_id = doc.get("id", "unknown_chunk")
        reason = f"Low eval score ({eval_score}) for query: '{query}'"
        
        # Call Qdrant service flag method
        qdrant_service.flag_chunk_for_reindex(chunk_id, reason)
        
        record = {
            "chunk_id": chunk_id,
            "query": query,
            "eval_score": eval_score,
            "flagged_at": int(time.time()),
            "reason": reason
        }
        flagged_records.append(record)
        FLAGGED_CHUNKS_LOG.append(record)

    print(f"[FLAGGED REINDEX] Flagged {len(flagged_records)} chunks due to low eval score ({eval_score}).")
    
    return {
        "graph_path": ["flag_reindex"]
    }
