import logging

from app.services.qdrant_client import qdrant_service

logger = logging.getLogger(__name__)


def flag_reindex_node(state):
    reason = f"Low answer evaluation score ({state['eval_score']:.3f})"
    failed = False
    for doc in state["documents"]:
        try:
            qdrant_service.flag_chunk_for_reindex(doc["id"], reason)
        except Exception:
            logger.exception("Could not flag a retrieved chunk")
            failed = True
    return {"error": "Some chunks could not be flagged for reindexing."} if failed else {}
