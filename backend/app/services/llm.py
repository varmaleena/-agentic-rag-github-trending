from functools import cached_property
from typing import Iterator, Protocol

from app.config import settings
from app.services.bedrock_client import bedrock_service
from app.services.telemetry import record_tokens


class LanguageModel(Protocol):
    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7,
                 *, json_schema: dict | None = None) -> str: ...

    def generate_stream(self, prompt: str, max_tokens: int = 1024,
                        temperature: float = 0.7) -> Iterator[str]: ...


class VertexClient:
    @cached_property
    def client(self):
        from google import genai
        from google.genai.types import HttpOptions

        if not settings.GOOGLE_CLOUD_PROJECT or not settings.GEMINI_MODEL:
            raise ValueError("Configure GOOGLE_CLOUD_PROJECT and GEMINI_MODEL for Vertex AI")
        return genai.Client(
            vertexai=True,
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.GOOGLE_CLOUD_LOCATION,
            http_options=HttpOptions(api_version="v1"),
        )

    def generate(self, prompt, max_tokens=1024, temperature=0.7, *, json_schema=None):
        config = {"max_output_tokens": max_tokens, "temperature": temperature}
        if json_schema is not None:
            config["response_mime_type"] = "application/json"
            config["response_json_schema"] = json_schema
        response = self.client.models.generate_content(
            model=settings.GEMINI_MODEL, contents=prompt, config=config
        )
        if usage := response.usage_metadata:
            record_tokens(usage.prompt_token_count, usage.candidates_token_count)
        return response.text or ""

    def generate_stream(self, prompt, max_tokens=1024, temperature=0.7):
        usage = None
        for chunk in self.client.models.generate_content_stream(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={"max_output_tokens": max_tokens, "temperature": temperature},
        ):
            if chunk.usage_metadata is not None:
                usage = chunk.usage_metadata
            if chunk.text:
                yield chunk.text
        if usage:
            record_tokens(usage.prompt_token_count, usage.candidates_token_count)


llm_service: LanguageModel = VertexClient() if settings.LLM_PROVIDER == "vertex" else bedrock_service
