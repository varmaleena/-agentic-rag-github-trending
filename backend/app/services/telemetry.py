from contextlib import contextmanager
from contextvars import ContextVar

from opentelemetry import trace

token_usage = ContextVar("token_usage", default=None)
tracer = trace.get_tracer("agentic-rag")


def record_tokens(input_tokens=None, output_tokens=None):
    usage = token_usage.get()
    if usage is not None:
        for key, value in (("input_tokens", input_tokens), ("output_tokens", output_tokens)):
            if value is not None:
                usage[key] = usage.get(key, 0) + value


@contextmanager
def node_span(name, retries):
    with tracer.start_as_current_span(f"rag.{name}") as span:
        span.set_attribute("rag.retries", retries)
        usage = {}
        token = token_usage.set(usage)
        try:
            yield span
        finally:
            token_usage.reset(token)
            for name, count in usage.items():
                span.set_attribute(f"gen_ai.usage.{name}", count)


def setup_tracing():
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(resource=Resource.create({"service.name": "agentic-rag"}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    return provider
