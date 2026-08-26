import pytest
from app.graph.state import AgentState
from app.graph.nodes.route_query import route_query_node

def test_agent_state_keys():
    """Verify that AgentState schema contains all required fields."""
    state = AgentState(
        query="What is LangGraph?",
        rewritten_query=None,
        documents=[],
        relevance_grade="yes",
        answer="",
        eval_score=0.9,
        retries=0,
        graph_path=["route_query"]
    )
    assert state["query"] == "What is LangGraph?"
    assert state["retries"] == 0

def test_route_query_fallback(mocker=None):
    """Test route query fallback logic when query is technical."""
    state = {"query": "Tell me about trending Python repositories on GitHub."}
    # Mock bedrock response if running offline
    res = route_query_node(state)
    assert "relevance_grade" in res
    assert res["relevance_grade"] in ["retrieve", "generate_direct"]
