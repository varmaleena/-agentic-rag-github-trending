import base64
import os
from datetime import date, timedelta

import httpx

GITHUB_API_URL = "https://api.github.com"


def github_client():
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Agentic-RAG-Ingestion"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    return httpx.Client(base_url=GITHUB_API_URL, headers=headers, timeout=15, follow_redirects=True)


def repository_with_readme(client, item):
    response = client.get(f"/repos/{item['full_name']}/readme")
    content = ""
    if response.status_code != 404:
        response.raise_for_status()
        readme = response.json()
        if readme["encoding"] != "base64":
            raise ValueError("Unsupported README encoding")
        content = base64.b64decode(readme["content"]).decode("utf-8", errors="replace")

    return {
        "repo_name": item["full_name"],
        "description": item.get("description") or "",
        "readme_content": content,
        "stars": item["stargazers_count"],
        "language": item.get("language") or "Unknown",
        "url": item["html_url"],
    }


def fetch_repository(repo_name):
    with github_client() as client:
        response = client.get(f"/repos/{repo_name}")
        response.raise_for_status()
        return repository_with_readme(client, response.json())


def fetch_trending_repos(limit=10, min_stars=50):
    cutoff = date.today() - timedelta(days=30)
    with github_client() as client:
        response = client.get("/search/repositories", params={
            "q": f"stars:>{min_stars} created:>={cutoff.isoformat()}",
            "sort": "stars",
            "order": "desc",
            "per_page": limit,
        })
        response.raise_for_status()
        return [repository_with_readme(client, item) for item in response.json()["items"]]
