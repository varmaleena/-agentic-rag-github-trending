import time
from typing import List, Dict, Any

def chunk_text(text: str, chunk_size: int = 1500, chunk_overlap: int = 200) -> List[str]:
    """
    Simple character-based text chunker approximating ~300-500 tokens per chunk with ~50 token overlap.
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += (chunk_size - chunk_overlap)

    return chunks

def chunk_repository(repo: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Takes a repository metadata dictionary and produces a list of enriched chunk objects
    with metadata: repo_name, url, stars, language, and ingested_at timestamp.
    """
    repo_name = repo.get("repo_name", "unknown")
    url = repo.get("url", "")
    description = repo.get("description", "")
    readme = repo.get("readme_content", "")
    stars = repo.get("stars", 0)
    language = repo.get("language", "Unknown")
    ingested_at = int(time.time())

    full_text = f"Repository: {repo_name}\nDescription: {description}\n\nREADME:\n{readme}"
    text_chunks = chunk_text(full_text)

    processed_chunks = []
    for idx, content in enumerate(text_chunks):
        chunk_id = f"{repo_name.replace('/', '_')}_chunk_{idx}"
        processed_chunks.append({
            "id": chunk_id,
            "text": content,
            "metadata": {
                "repo_name": repo_name,
                "url": url,
                "stars": stars,
                "language": language,
                "chunk_index": idx,
                "ingested_at": ingested_at
            }
        })

    return processed_chunks

if __name__ == "__main__":
    sample_repo = {
        "repo_name": "example/trending-repo",
        "url": "https://github.com/example/trending-repo",
        "description": "High performance text processing framework.",
        "readme_content": "This is a long README file " * 100,
        "stars": 1200,
        "language": "Python"
    }
    chunks = chunk_repository(sample_repo)
    print(f"Generated {len(chunks)} chunks for {sample_repo['repo_name']}.")
