from typing import Dict, Any
from app.services.bedrock_client import bedrock_service

def generate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node that calls AWS Bedrock with the query and retrieved context chunks
    to synthesize a complete answer.
    """
    query = state.get("query", "")
    documents = state.get("documents", [])
    
    # Format retrieved document context
    context_str = ""
    if documents:
        formatted_chunks = []
        for i, doc in enumerate(documents, start=1):
            payload = doc.get("payload", doc)
            repo = payload.get("repo_name", "Unknown Repo")
            content = payload.get("text", payload.get("content", str(doc)))
            formatted_chunks.append(f"--- Document {i} (Repo: {repo}) ---\n{content}")
        context_str = "\n\n".join(formatted_chunks)
    else:
        context_str = "No specific vector context available."

    prompt = f"""You are an expert AI assistant specializing in GitHub trending repositories.
Answer the user query concisely and accurately using the provided repository context documents.

Context:
{context_str}

User Query: {query}

Answer:"""

    answer = bedrock_service.generate(prompt=prompt, max_tokens=1024, temperature=0.3)

    return {
        "answer": answer
    }
