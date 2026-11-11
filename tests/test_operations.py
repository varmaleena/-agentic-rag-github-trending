from unittest.mock import Mock

import pytest
from mcp import Client
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.retriever_mcp import server
from app.services import history, telemetry
from app.services.embeddings import embedding_service
from app.services.qdrant_client import qdrant_service


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_mcp_retriever(monkeypatch):
    monkeypatch.setattr(embedding_service, "embed_text", Mock(return_value=[1.0]))
    search = Mock(return_value=[{
        "id": 1, "score": 0.9, "payload": {"repo_name": "example/repo", "text": "A README"},
    }])
    monkeypatch.setattr(qdrant_service, "search_similar", search)
    async with Client(server) as client:
        tools = await client.list_tools()
        assert tools.tools[0].annotations.read_only_hint
        response = await client.call_tool("retrieve_repositories", {"query": " example ", "limit": 2})
        assert not response.is_error
        assert "example/repo" in response.content[0].text
    search.assert_called_once_with([1.0], top_k=2)


def test_history_persists_and_omits_null_scores():
    history.save({"query": "One", "latency_seconds": 2.0, "eval_score": 0.5})
    history.save({"query": "Two", "latency_seconds": 4.0, "eval_score": None})
    stats = history.stats()
    assert stats["total_queries"] == 2
    assert stats["avg_latency_seconds"] == 3.0
    assert stats["avg_eval_score"] == 0.5
    assert [row["query"] for row in stats["recent_queries"]] == ["Two", "One"]


def test_trace_exports_retry_count_and_actual_usage(monkeypatch):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(telemetry, "tracer", provider.get_tracer("test"))

    with telemetry.node_span("generate", 2):
        telemetry.record_tokens(41, 7)

    span, = exporter.get_finished_spans()
    assert span.name == "rag.generate"
    assert span.attributes["rag.retries"] == 2
    assert span.attributes["gen_ai.usage.input_tokens"] == 41
    assert span.attributes["gen_ai.usage.output_tokens"] == 7
    assert span.end_time >= span.start_time
    provider.shutdown()


def test_vertex_uses_schema_and_streams_model_text(monkeypatch):
    from app.config import settings
    from app.services.llm import VertexClient

    monkeypatch.setattr(settings, "GEMINI_MODEL", "test-model")
    provider = VertexClient()
    provider.client = Mock()
    models = provider.client.models
    models.generate_content.return_value = Mock(text='{"relevance":"yes"}', usage_metadata=None)
    models.generate_content_stream.return_value = [
        Mock(text="Answer", usage_metadata=None),
        Mock(text=" fragment", usage_metadata=None),
    ]
    schema = {"type": "object"}
    assert provider.generate("Judge", json_schema=schema) == '{"relevance":"yes"}'
    assert models.generate_content.call_args.kwargs["config"]["response_json_schema"] == schema
    assert list(provider.generate_stream("Answer")) == ["Answer", " fragment"]
