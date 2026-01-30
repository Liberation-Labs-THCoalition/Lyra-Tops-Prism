"""Data models for arXiv MCP server."""

import dataclasses
from dataclasses import dataclass, field
from enum import Enum


class PaperSource(str, Enum):
    ARXIV_SEARCH = "arxiv_search"
    CITATION_GRAPH = "citation_graph"
    MANUAL = "manual"


@dataclass
class Paper:
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    categories: list[str]
    published: str
    updated: str
    pdf_url: str
    entry_url: str
    downloaded: bool = False
    pdf_path: str = ""
    source_path: str = ""
    full_text: str = ""
    added_at: str = ""
    source: PaperSource = PaperSource.ARXIV_SEARCH
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    reading_list: bool = False

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["source"] = self.source.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Paper":
        defaults = {
            "arxiv_id": "",
            "title": "",
            "authors": [],
            "abstract": "",
            "categories": [],
            "published": "",
            "updated": "",
            "pdf_url": "",
            "entry_url": "",
            "downloaded": False,
            "pdf_path": "",
            "source_path": "",
            "full_text": "",
            "added_at": "",
            "source": PaperSource.ARXIV_SEARCH,
            "tags": [],
            "notes": "",
            "reading_list": False,
        }
        merged = {**defaults, **d}
        if isinstance(merged["source"], str):
            merged["source"] = PaperSource(merged["source"])
        return cls(**{k: merged[k] for k in defaults})


@dataclass
class Citation:
    title: str
    authors: list[str]
    arxiv_id: str = ""
    doi: str = ""
    semantic_scholar_id: str = ""
    year: int = 0
    context: str = ""


@dataclass
class ResearchSession:
    session_id: str
    name: str
    created_at: str
    papers: list[str] = field(default_factory=list)
    notes: str = ""
    active: bool = True

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ResearchSession":
        defaults = {
            "session_id": "",
            "name": "",
            "created_at": "",
            "papers": [],
            "notes": "",
            "active": True,
        }
        merged = {**defaults, **d}
        return cls(**{k: merged[k] for k in defaults})


@dataclass
class ReadingListEntry:
    arxiv_id: str
    added_at: str
    priority: int = 3
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    read: bool = False

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ReadingListEntry":
        defaults = {
            "arxiv_id": "",
            "added_at": "",
            "priority": 3,
            "tags": [],
            "notes": "",
            "read": False,
        }
        merged = {**defaults, **d}
        return cls(**{k: merged[k] for k in defaults})
