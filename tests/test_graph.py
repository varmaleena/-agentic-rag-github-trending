from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.graph.graph import app_graph
from app.main import app
from app.services.llm import llm_service
from app.services.embeddings import embedding_service
from app.services.qdrant_client import qdrant_service


@pytest.fixture
def services(monkeypatch):
    document = {"id": 1, "payload": {"repo_name": "org/repo", "text": "Reference text"}}
    llm = Mock()
    retrieval = Mock(return_value=[document])
    flag = Mock()
    monkeypatch.setattr(llm_service, "generate", llm)
    monkeypatch.setattr(llm_service, "generate_stream", Mock(return_value=iter(["Real ", "answer"])))
    monkeypatch.setattr(embedding_service, "embed_text", lambda query: [query])
    monkeypatch.setattr(qdrant_service, "search_similar", retrieval)
    monkeypatch.setattr(qdrant_service, "flag_chunk_for_reindex", flag)
    return llm, retrieval, flag


def test_retry_cap(services, monkeypatch):
    monkeypatch.setattr(settings, "MAX_RETRIEVAL_RETRIES", 3)
    llm, retrieval, flag = services
    llm.side_effect = ["retrieve", '{"relevance":"no"}', "rewrite one",
                       '{"relevance":"no"}', "rewrite two", '{"relevance":"no"}',
                       "rewrite three", '{"relevance":"no"}']
    state = app_graph.invoke({"query": "Question"})
    assert state["retries"] == 3
    assert retrieval.call_count == 4
    assert state["graph_path"].count("rewrite_query") == 3
    assert state["eval_score"] is None
    flag.assert_not_called()


def test_websocket_corrective_run(services):
    llm, retrieval, _ = services
    llm.side_effect = ["retrieve", '{"relevance":"no"}', "better query",
                       '```json\n{"relevance":"yes"}\n```', '{"faithfulness":1,"relevancy":0.8}']
    with TestClient(app).websocket_connect("/ws/chat") as ws:
        ws.send_json({"query": "Question"})
        events = []
        while True:
            event = ws.receive_json()
            if event["type"] in {"stream_end", "error"}:
                break
            events.append(event)
    assert event["type"] == "stream_end"
    assert event["retries"] == 1
    assert event["eval_score"] == pytest.approx(0.9)
    assert event["graph_path"] == [
        "route_query", "retrieve", "grade_documents", "rewrite_query",
        "retrieve", "grade_documents", "generate", "evaluate",
    ]
    assert [e["node"] for e in events if e["type"] == "node_transition"] == event["graph_path"]
    assert "".join(e["content"] for e in events if e["type"] == "token") == "Real answer"
    assert retrieval.call_args.kwargs["query_vector"] == ["better query"]


@pytest.mark.parametrize(("score", "should_flag"), [(0.69, True), (0.7, False), (0.8, False)])
def test_evaluation_threshold(services, monkeypatch, score, should_flag):
    monkeypatch.setattr(settings, "EVAL_SCORE_THRESHOLD", 0.7)
    llm, _, flag = services
    llm.side_effect = ["retrieve", '{"relevance":"yes"}',
                       f'{{"faithfulness":{score},"relevancy":{score}}}']
    state = app_graph.invoke({"query": "Question"})
    assert state["eval_score"] == score
    assert ("flag_reindex" in state["graph_path"]) == should_flag
    if should_flag:
        flag.assert_called_once_with(1, "Low answer evaluation score (0.690)")
    else:
        flag.assert_not_called()


def test_invalid_route_defaults_to_retrieval(services):
    llm, retrieval, _ = services
    llm.side_effect = ["unclear", '{"relevance":"yes"}', '{"faithfulness":1,"relevancy":1}']
    app_graph.invoke({"query": "Question"})
    retrieval.assert_called_once()


@pytest.mark.parametrize("bad_grade", [True, False])
def test_invalid_judge_output(services, bad_grade):
    llm, _, flag = services
    llm.side_effect = ["retrieve", "{}"] if bad_grade else ["retrieve", '{"relevance":"yes"}', "{}"]
    state = app_graph.invoke({"query": "Question"})
    assert state.get("eval_score") is None
    assert state["error"]
    assert bool(state.get("answer")) is not bad_grade
    flag.assert_not_called()
