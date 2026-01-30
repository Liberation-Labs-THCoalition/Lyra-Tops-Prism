"""Semantic Scholar API client for citation graph exploration."""

import httpx
from typing import Optional
import config
from models import Citation


async def _api_get(endpoint: str, params: Optional[dict] = None) -> dict:
    """Make a GET request to Semantic Scholar API."""
    headers = {}
    if config.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = config.SEMANTIC_SCHOLAR_API_KEY

    url = f"{config.SEMANTIC_SCHOLAR_BASE_URL}/{endpoint}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()


def _s2_paper_to_citation(paper: dict) -> Citation:
    """Convert Semantic Scholar paper dict to Citation."""
    arxiv_id = ""
    if paper.get("externalIds", {}).get("ArXiv"):
        arxiv_id = paper["externalIds"]["ArXiv"]

    authors = [a.get("name", "") for a in paper.get("authors", [])]

    return Citation(
        title=paper.get("title", ""),
        authors=authors[:10],
        arxiv_id=arxiv_id,
        doi=paper.get("externalIds", {}).get("DOI", ""),
        semantic_scholar_id=paper.get("paperId", ""),
        year=paper.get("year") or 0,
    )


async def get_citations(arxiv_id: str, limit: int = 50) -> list[Citation]:
    """Get papers that cite this paper (forward citations).

    Args:
        arxiv_id: arXiv paper ID
        limit: Max citations to return

    Returns:
        List of citing papers as Citation objects
    """
    fields = "title,authors,year,externalIds"
    data = await _api_get(
        f"paper/ARXIV:{arxiv_id}/citations",
        params={"fields": fields, "limit": limit}
    )

    citations = []
    for item in data.get("data", []):
        citing_paper = item.get("citingPaper", {})
        if citing_paper.get("title"):
            citations.append(_s2_paper_to_citation(citing_paper))
    return citations


async def get_references(arxiv_id: str, limit: int = 50) -> list[Citation]:
    """Get papers this paper references (backward citations).

    Args:
        arxiv_id: arXiv paper ID
        limit: Max references to return

    Returns:
        List of referenced papers as Citation objects
    """
    fields = "title,authors,year,externalIds"
    data = await _api_get(
        f"paper/ARXIV:{arxiv_id}/references",
        params={"fields": fields, "limit": limit}
    )

    references = []
    for item in data.get("data", []):
        cited_paper = item.get("citedPaper", {})
        if cited_paper.get("title"):
            references.append(_s2_paper_to_citation(cited_paper))
    return references


async def get_related(arxiv_id: str) -> list[Citation]:
    """Get recommended related papers via Semantic Scholar.

    Uses the recommendations API which has a different base URL
    from the graph API.

    Args:
        arxiv_id: arXiv paper ID

    Returns:
        List of related papers as Citation objects
    """
    headers = {}
    if config.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = config.SEMANTIC_SCHOLAR_API_KEY

    url = f"https://api.semanticscholar.org/recommendations/v1/papers/forpaper/ARXIV:{arxiv_id}"
    fields = "title,authors,year,externalIds"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params={"fields": fields, "limit": 20}, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    related = []
    for paper in data.get("recommendedPapers", []):
        if paper.get("title"):
            related.append(_s2_paper_to_citation(paper))
    return related
