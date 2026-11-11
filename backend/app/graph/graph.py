from functools import wraps

from langgraph.config import get_stream_writer
from langgraph.graph import END, StateGraph

from app.config import settings
from app.graph.nodes.evaluate import evaluate_node
from app.graph.nodes.flag_reindex import flag_reindex_node
from app.graph.nodes.generate import generate_node
from app.graph.nodes.grade_documents import grade_documents_node
from app.graph.nodes.retrieve import retrieve_node
from app.graph.nodes.rewrite_query import rewrite_query_node
from app.graph.nodes.route_query import route_query_node
from app.graph.state import AgentState


def decide_to_route(state):
    return "generate" if state["relevance_grade"] == "generate_direct" else "retrieve"


def decide_to_generate_or_rewrite(state):
    if state["relevance_grade"] == "error":
        return END
    if state["relevance_grade"] == "yes" or state["retries"] >= settings.MAX_RETRIEVAL_RETRIES:
        return "generate"
    return "rewrite_query"


def decide_eval_outcome(state):
    score = state.get("eval_score")
    if score is not None and score < settings.EVAL_SCORE_THRESHOLD:
        return "flag_reindex"
    return END


def tracked(name, node):
    @wraps(node)
    def execute(state):
        get_stream_writer()({"type": "node_transition", "node": name, "status": "active"})
        return {**node(state), "graph_path": [name]}

    return execute


def build_graph(*, corrective=True, write_reindex_flags=True):
    workflow = StateGraph(AgentState)
    nodes = {
        "route_query": route_query_node,
        "retrieve": retrieve_node,
        "grade_documents": grade_documents_node,
        "rewrite_query": rewrite_query_node,
        "generate": generate_node,
        "evaluate": evaluate_node,
        "flag_reindex": flag_reindex_node,
    }
    if not corrective:
        nodes.pop("route_query")
        nodes.pop("grade_documents")
        nodes.pop("rewrite_query")
    if not write_reindex_flags:
        nodes.pop("flag_reindex")
    for name, node in nodes.items():
        workflow.add_node(name, tracked(name, node))

    if corrective:
        workflow.set_entry_point("route_query")
        workflow.add_conditional_edges("route_query", decide_to_route, ["retrieve", "generate"])
        workflow.add_edge("retrieve", "grade_documents")
        workflow.add_conditional_edges(
            "grade_documents", decide_to_generate_or_rewrite, ["generate", "rewrite_query", END]
        )
        workflow.add_edge("rewrite_query", "retrieve")
    else:
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")

    workflow.add_edge("generate", "evaluate")
    if write_reindex_flags:
        workflow.add_conditional_edges("evaluate", decide_eval_outcome, ["flag_reindex", END])
        workflow.add_edge("flag_reindex", END)
    else:
        workflow.add_edge("evaluate", END)

    return workflow.compile()


app_graph = build_graph()
