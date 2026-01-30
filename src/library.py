"""JSON-based paper library — Phase 1."""

import json

import config
from models import Paper, ReadingListEntry


def load_library() -> list[Paper]:
    """Read library.json and return list of Papers."""
    if not config.LIBRARY_PATH.exists():
        return []
    with open(config.LIBRARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Paper.from_dict(d) for d in data]


def save_library(papers: list[Paper]) -> None:
    """Write list of Papers to library.json."""
    config.ensure_dirs()
    with open(config.LIBRARY_PATH, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in papers], f, indent=2)


def add_paper(paper: Paper) -> None:
    """Add paper to library if not already present (by arxiv_id)."""
    papers = load_library()
    if any(p.arxiv_id == paper.arxiv_id for p in papers):
        return
    papers.append(paper)
    save_library(papers)


def get_paper(arxiv_id: str) -> Paper | None:
    """Find a paper by arxiv_id."""
    papers = load_library()
    for p in papers:
        if p.arxiv_id == arxiv_id:
            return p
    return None


def update_paper(arxiv_id: str, updates: dict) -> None:
    """Update fields on a paper and save."""
    papers = load_library()
    for p in papers:
        if p.arxiv_id == arxiv_id:
            for key, value in updates.items():
                if hasattr(p, key):
                    setattr(p, key, value)
            break
    save_library(papers)


def load_reading_list() -> list[ReadingListEntry]:
    """Read reading_list.json."""
    if not config.READING_LIST_PATH.exists():
        return []
    with open(config.READING_LIST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [ReadingListEntry.from_dict(d) for d in data]


def save_reading_list(entries: list[ReadingListEntry]) -> None:
    """Write reading list to JSON."""
    config.ensure_dirs()
    with open(config.READING_LIST_PATH, "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in entries], f, indent=2)
