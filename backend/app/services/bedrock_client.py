import json

import boto3

from app.config import settings
from app.services.telemetry import record_tokens


class BedrockClient:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
        return self._client

    def _request(self, prompt, max_tokens, temperature):
        return {
            "modelId": settings.BEDROCK_MODEL_ID,
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
        }

    def generate(self, prompt, max_tokens=1024, temperature=0.7, *, json_schema=None):
        request = self._request(prompt, max_tokens, temperature)
        if json_schema is not None:
            request["toolConfig"] = {
                "tools": [{"toolSpec": {
                    "name": "submit_result",
                    "description": "Return the requested judgment as structured data.",
                    "inputSchema": {"json": json_schema},
                }}],
                "toolChoice": {"tool": {"name": "submit_result"}},
            }
        response = self.client.converse(**request)
        usage = response.get("usage", {})
        record_tokens(usage.get("inputTokens"), usage.get("outputTokens"))
        blocks = response["output"]["message"]["content"]
        if json_schema is not None:
            results = [block["toolUse"]["input"] for block in blocks
                       if block.get("toolUse", {}).get("name") == "submit_result"]
            if len(results) != 1:
                raise ValueError("Bedrock did not return one structured judgment")
            return json.dumps(results[0])
        return "".join(block.get("text", "") for block in blocks)

    def generate_stream(self, prompt, max_tokens=1024, temperature=0.7):
        response = self.client.converse_stream(**self._request(prompt, max_tokens, temperature))
        stream = response["stream"]
        try:
            for event in stream:
                if any(key.lower().endswith("exception") for key in event):
                    raise RuntimeError("Bedrock stream returned an error")
                if usage := event.get("metadata", {}).get("usage"):
                    record_tokens(usage.get("inputTokens"), usage.get("outputTokens"))
                token = event.get("contentBlockDelta", {}).get("delta", {}).get("text")
                if token:
                    yield token
        finally:
            stream.close()


bedrock_service = BedrockClient()
