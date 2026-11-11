import json
import re


def context_json(documents):
    """Serialize only the source fields needed by the model."""
    return json.dumps([
        {"repo": payload.get("repo_name"), "text": payload.get("text", "")}
        for doc in documents
        for payload in [doc.get("payload", doc)]
    ])


def parse_judge_json(response):
    response = response.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", response, re.DOTALL | re.IGNORECASE)
    return json.loads(fenced[1] if fenced else response)
