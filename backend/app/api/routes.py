import logging
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.graph.graph import app_graph

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["RAG Queries"])
QUERY_HISTORY = []


def graph_config():
    return {"recursion_limit": 8 + 3 * settings.MAX_RETRIEVAL_RETRIES}


def record_query_history(state, latency_seconds):
    record = {
        "query": state["query"],
        "answer": state.get("answer", ""),
        "eval_score": state.get("eval_score"),
        "error": state.get("error"),
        "retries": state["retries"],
        "graph_path": state["graph_path"],
        "latency_seconds": round(latency_seconds, 3),
        "timestamp": int(time.time()),
    }
    QUERY_HISTORY.append(record)
    return record


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    answer: str
    eval_score: float | None
    error: str | None
    retries: int
    graph_path: list[str]
    latency_seconds: float
    timestamp: int


@router.post("/query", response_model=QueryResponse)
async def execute_query(req: QueryRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(400, "Query string cannot be empty.")

    started = time.monotonic()
    try:
        state = await app_graph.ainvoke({"query": query}, config=graph_config())
    except Exception:
        logger.exception("Query execution failed")
        raise HTTPException(502, "Query execution failed.") from None

    record = record_query_history(state, time.monotonic() - started)
    if not record["answer"]:
        raise HTTPException(502, record["error"])
    return record


@router.get("/dashboard/stats")
async def get_dashboard_stats():
    total = len(QUERY_HISTORY)
    scores = [q["eval_score"] for q in QUERY_HISTORY if q["eval_score"] is not None]
    return {
        "last_ingested_at": None,
        "total_queries": total,
        "avg_latency_seconds": round(sum(q["latency_seconds"] for q in QUERY_HISTORY) / total, 3) if total else 0,
        "avg_eval_score": round(sum(scores) / len(scores), 3) if scores else None,
        "recent_queries": list(reversed(QUERY_HISTORY[-20:])),
    }
