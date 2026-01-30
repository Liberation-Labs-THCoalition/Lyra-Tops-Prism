"""Configuration for arXiv MCP server."""

import os
from pathlib import Path

DATA_DIR = Path(os.getenv("ARXIV_DATA_DIR", str(Path.home() / ".arxiv-mcp")))
PAPERS_DIR = DATA_DIR / "papers"
LIBRARY_PATH = DATA_DIR / "library.json"
READING_LIST_PATH = DATA_DIR / "reading_list.json"
SESSIONS_DIR = DATA_DIR / "sessions"

SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
SEMANTIC_SCHOLAR_BASE_URL = "https://api.semanticscholar.org/graph/v1"

ARXIV_RATE_LIMIT_SECONDS = float(os.getenv("ARXIV_RATE_LIMIT_SECONDS", "3"))


def ensure_dirs():
    """Create data directories if they don't exist."""
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
