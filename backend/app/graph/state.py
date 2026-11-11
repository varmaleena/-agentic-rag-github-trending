import operator
from typing import Annotated, Any, TypedDict


class AgentState(TypedDict, total=False):
    query: str
    rewritten_query: str
    documents: list[dict[str, Any]]
    relevance_grade: str
    answer: str
    reference_answer: str
    eval_score: float | None
    faithfulness: float
    relevancy: float
    error: str
    retries: Annotated[int, operator.add]
    graph_path: Annotated[list[str], operator.add]
