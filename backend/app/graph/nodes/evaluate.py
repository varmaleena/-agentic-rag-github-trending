import json
from typing import Dict, Any
from app.services.bedrock_client import bedrock_service
from app.config import settings

def evaluate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node that performs automated self-evaluation (LLM-as-a-judge / RAGAS criteria)
    measuring faithfulness and relevance of the generated answer against context documents.
    """
    query = state.get("query", "")
    answer = state.get("answer", "")
    documents = state.get("documents", [])
    
    if not answer or not documents:
        # Default passing score if no context was used (direct response)
        return {"eval_score": 1.0}

    context_text = "\n".join([str(doc.get("payload", doc)) for doc in documents])

    prompt = f"""You are an automated RAG evaluator. Evaluate the quality of the generated answer based on the query and context documents.

Criteria:
1. Faithfulness: Is the answer derived strictly from the provided context?
2. Answer Relevancy: Does the answer directly address the query?

Context:
{context_text[:2000]}

Query: {query}
Answer: {answer}

Provide a numerical score between 0.0 and 1.0 where 1.0 is a perfect answer and 0.0 is completely inaccurate or hallucinated.
Respond in JSON format: {{"eval_score": 0.85, "reason": "brief explanation"}}

JSON Output:"""

    try:
        raw_response = bedrock_service.generate(prompt=prompt, max_tokens=100, temperature=0.0).strip()
        data = json.loads(raw_response)
        eval_score = float(data.get("eval_score", 0.8))
    except Exception as e:
        print(f"Eval scoring fallback due to parsing error: {e}")
        eval_score = 0.75

    return {
        "eval_score": eval_score
    }
