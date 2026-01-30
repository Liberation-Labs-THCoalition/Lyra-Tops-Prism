"""arXiv API client wrapper with async interface."""

import asyncio
import arxiv
from models import Paper, PaperSource
from datetime import datetime
import config


def _result_to_paper(result: arxiv.Result) -> Paper:
    """Convert arxiv.Result to our Paper model."""
    # Extract arxiv_id from entry_id URL: http://arxiv.org/abs/2301.07041v1 -> 2301.07041
    entry_id = result.entry_id
    arxiv_id = entry_id.split("/abs/")[-1].split("v")[0] if "/abs/" in entry_id else entry_id

    return Paper(
        arxiv_id=arxiv_id,
        title=result.title.replace("\n", " ").strip(),
        authors=[str(a) for a in result.authors],
        abstract=result.summary.replace("\n", " ").strip(),
        categories=[c for c in result.categories],
        published=result.published.isoformat() if result.published else "",
        updated=result.updated.isoformat() if result.updated else "",
        pdf_url=result.pdf_url or "",
        entry_url=result.entry_id or "",
        added_at=datetime.now().isoformat(),
        source=PaperSource.ARXIV_SEARCH,
    )


def _search_sync(query: str, max_results: int = 10, sort_by: str = "relevance") -> list[Paper]:
    """Synchronous search."""
    sort_map = {
        "relevance": arxiv.SortCriterion.Relevance,
        "submitted": arxiv.SortCriterion.SubmittedDate,
        "updated": arxiv.SortCriterion.LastUpdatedDate,
    }
    criterion = sort_map.get(sort_by, arxiv.SortCriterion.Relevance)

    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=max_results, sort_by=criterion)

    papers = []
    for result in client.results(search):
        papers.append(_result_to_paper(result))
    return papers


def _get_paper_sync(arxiv_id: str) -> Paper:
    """Synchronous single paper fetch."""
    client = arxiv.Client()
    search = arxiv.Search(id_list=[arxiv_id])
    results = list(client.results(search))
    if not results:
        raise ValueError(f"Paper not found: {arxiv_id}")
    return _result_to_paper(results[0])


def _download_pdf_sync(arxiv_id: str) -> str:
    """Download PDF, return local path."""
    config.ensure_dirs()
    paper_dir = config.PAPERS_DIR / arxiv_id.replace("/", "_")
    paper_dir.mkdir(parents=True, exist_ok=True)

    client = arxiv.Client()
    search = arxiv.Search(id_list=[arxiv_id])
    result = next(client.results(search))

    dest = str(paper_dir / "paper.pdf")
    result.download_pdf(dirpath=str(paper_dir), filename="paper.pdf")
    return dest


def _download_source_sync(arxiv_id: str) -> str:
    """Download LaTeX source, return local path."""
    config.ensure_dirs()
    paper_dir = config.PAPERS_DIR / arxiv_id.replace("/", "_")
    paper_dir.mkdir(parents=True, exist_ok=True)

    client = arxiv.Client()
    search = arxiv.Search(id_list=[arxiv_id])
    result = next(client.results(search))

    dest = str(paper_dir / "source.tar.gz")
    result.download_source(dirpath=str(paper_dir), filename="source.tar.gz")
    return dest


# Async public API

async def search(query: str, max_results: int = 10, sort_by: str = "relevance") -> list[Paper]:
    return await asyncio.to_thread(_search_sync, query, max_results, sort_by)

async def get_paper(arxiv_id: str) -> Paper:
    return await asyncio.to_thread(_get_paper_sync, arxiv_id)

async def download_pdf(arxiv_id: str) -> str:
    return await asyncio.to_thread(_download_pdf_sync, arxiv_id)

async def download_source(arxiv_id: str) -> str:
    return await asyncio.to_thread(_download_source_sync, arxiv_id)
