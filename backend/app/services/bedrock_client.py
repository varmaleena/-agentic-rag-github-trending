import json

import boto3

from app.config import settings


class BedrockClient:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
        return self._client

    def _body(self, prompt, max_tokens, temperature):
        return json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        })

    def generate(self, prompt, max_tokens=1024, temperature=0.7, *, json_output=False):
        response = self.client.invoke_model(
            modelId=settings.BEDROCK_MODEL_ID, body=self._body(prompt, max_tokens, temperature)
        )
        return json.load(response["body"])["content"][0]["text"]

    def generate_stream(self, prompt, max_tokens=1024, temperature=0.7):
        response = self.client.invoke_model_with_response_stream(
            modelId=settings.BEDROCK_MODEL_ID, body=self._body(prompt, max_tokens, temperature)
        )
        stream = response["body"]
        try:
            for event in stream:
                if "chunk" not in event:
                    raise RuntimeError("Bedrock stream returned an error")
                data = json.loads(event["chunk"]["bytes"])
                if data["type"] == "content_block_delta" and data["delta"].get("text"):
                    yield data["delta"]["text"]
        finally:
            stream.close()


bedrock_service = BedrockClient()
