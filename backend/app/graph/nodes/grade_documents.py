from typing import Dict, Any
from app.services.bedrock_client import bedrock_service

def grade_documents_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node that evaluates whether retrieved document chunks are relevant
    to the user query using an LLM call via Bedrock.
    
    Returns:
        Dict[str, Any]: State update containing 'relevance_grade' ("yes" or "no").
    """
    query = state.get("query", "")
    documents = state.get("documents", [])
    
    if not documents:
        print("[Grade Documents] No documents retrieved. Grade: no")
        return {"relevance_grade": "no"}

    # Format document contents for LLM grading
    formatted_docs = []
    for i, doc in enumerate(documents, 1):
        payload = doc.get("payload", doc)
        text = payload.get("text", str(doc))
        formatted_docs.append(f"Document {i}: {text[:500]}")
    
    context = "\n\n".join(formatted_docs)

    prompt = f"""You are a document relevance grader for an agentic retrieval system.
Analyze the user query and the retrieved documents below to determine if AT LEAST ONE document is relevant to answering the query.

User Query: "{query}"

Retrieved Documents:
{context}

Grade the relevance of the documents. Respond with ONLY one word: "yes" if the documents contain relevant information, or "no" if they are irrelevant.

Relevance Grade:"""

    try:
        raw_grade = bedrock_service.generate(prompt=prompt, max_tokens=10, temperature=0.0).strip().lower()
        grade = "yes" if "yes" in raw_grade else "no"
    except Exception as e:
        print(f"[Grade Documents Fallback] Error grading documents: {e}")
        grade = "yes"  # Default fallback grade

    print(f"[Grade Documents] Query: '{query}' -> Relevance Grade: '{grade}'")

    return {
        "relevance_grade": grade
    }
