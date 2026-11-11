import logging
import time

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.config import settings
from app.graph.graph import app_graph
from app.services import history
from app.services.telemetry import tracer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["RAG Queries"])


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
    history.save(record)
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
        with tracer.start_as_current_span("rag.query"):
            state = await app_graph.ainvoke({"query": query}, config=graph_config())
    except Exception:
        logger.exception("Query execution failed")
        raise HTTPException(502, "Query execution failed.") from None

    record = await run_in_threadpool(record_query_history, state, time.monotonic() - started)
    if not record["answer"]:
        raise HTTPException(502, record["error"])
    return record


@router.get("/dashboard/stats")
async def get_dashboard_stats():
    return await run_in_threadpool(history.stats)
