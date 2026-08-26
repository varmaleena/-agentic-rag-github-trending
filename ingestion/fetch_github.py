import os
import httpx
import base64
from typing import List, Dict, Any

GITHUB_API_URL = "https://api.github.com"

def fetch_trending_repos(limit: int = 10, min_stars: int = 50) -> List[Dict[str, Any]]:
    """
    Fetches recently created/starred trending GitHub repositories via the GitHub REST API.
    Returns repo name, description, README content, stars, language, and URL.
    """
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Agentic-RAG-Ingestion"
    }
    if token:
        headers["Authorization"] = f"token {token}"

    # Search for repositories created or active recently sorted by stars
    query = f"stars:>{min_stars}"
    search_url = f"{GITHUB_API_URL}/search/repositories?q={query}&sort=stars&order=desc&per_page={limit}"

    repos = []
    with httpx.Client(headers=headers, timeout=15.0) as client:
        res = client.get(search_url)
        if res.status_code != 200:
            print(f"GitHub API Error: {res.status_code} - {res.text}")
            return repos
        
        items = res.json().get("items", [])
        for item in items:
            owner = item["owner"]["login"]
            repo_name = item["name"]
            full_name = item["full_name"]
            
            # Fetch README content for the repo
            readme_url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/readme"
            readme_res = client.get(readme_url)
            readme_content = ""
            if readme_res.status_code == 200:
                readme_data = readme_res.json()
                if readme_data.get("encoding") == "base64":
                    try:
                        readme_content = base64.b64decode(readme_data["content"]).decode("utf-8", errors="ignore")
                    except Exception:
                        readme_content = ""

            repos.append({
                "repo_name": full_name,
                "description": item.get("description") or "",
                "readme_content": readme_content,
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language") or "Unknown",
                "url": item.get("html_url", ""),
                "pushed_at": item.get("pushed_at", "")
            })

    return repos

if __name__ == "__main__":
    print("Testing GitHub API fetcher...")
    fetched = fetch_trending_repos(limit=2)
    print(f"Fetched {len(fetched)} repositories.")
    for r in fetched:
        print(f"- {r['repo_name']} ({r['stars']} stars, {r['language']})")
