import dataclasses
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import FastMCP

import config
import arxiv_client
import library
import pdf_extractor
import latex_extractor
import citation_graph
import session
from models import Paper, Citation, ReadingListEntry
from pathlib import Path

mcp = FastMCP("arxiv")


@mcp.tool()
async def arxiv_search(query: str, max_results: int = 10, sort_by: str = "relevance") -> str:
    """Search arXiv for papers.

    Args:
        query: Search query. Supports arXiv syntax: ti:, au:, abs:, cat:, all: with AND/OR/ANDNOT
        max_results: Maximum results (default 10, max 2000)
        sort_by: relevance, submitted, or updated

    Returns:
        JSON with paper metadata list
    """
    try:
        papers = await arxiv_client.search(query, min(max_results, 2000), sort_by)
        # Auto-add to library
        for p in papers:
            library.add_paper(p)
        return json.dumps({
            "success": True,
            "count": len(papers),
            "papers": [p.to_dict() for p in papers]
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def arxiv_get_paper(arxiv_id: str) -> str:
    """Get metadata for a single paper by arXiv ID.

    Args:
        arxiv_id: arXiv paper ID (e.g. "2301.07041")

    Returns:
        JSON with paper metadata
    """
    try:
        paper = await arxiv_client.get_paper(arxiv_id)
        library.add_paper(paper)
        return json.dumps({"success": True, "paper": paper.to_dict()})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def arxiv_browse_category(category: str, max_results: int = 20) -> str:
    """Browse recent papers in an arXiv category.

    Args:
        category: arXiv category (e.g. cs.AI, cs.CL, math.CO, physics.quant-ph)
        max_results: Number of recent papers (default 20)

    Returns:
        JSON with recent papers in category
    """
    try:
        papers = await arxiv_client.search(f"cat:{category}", max_results, "submitted")
        for p in papers:
            library.add_paper(p)
        return json.dumps({
            "success": True,
            "category": category,
            "count": len(papers),
            "papers": [p.to_dict() for p in papers]
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def arxiv_advanced_search(
    title: str = "",
    author: str = "",
    abstract: str = "",
    category: str = "",
    max_results: int = 10,
    sort_by: str = "relevance"
) -> str:
    """Search arXiv with field-specific filters.

    Args:
        title: Search in title field
        author: Search by author name
        abstract: Search in abstract
        category: Filter by category (e.g. cs.AI)
        max_results: Maximum results (default 10)
        sort_by: relevance, submitted, or updated

    Returns:
        JSON with matching papers
    """
    try:
        parts = []
        if title:
            parts.append(f"ti:{title}")
        if author:
            parts.append(f"au:{author}")
        if abstract:
            parts.append(f"abs:{abstract}")
        if category:
            parts.append(f"cat:{category}")

        if not parts:
            return json.dumps({"success": False, "error": "At least one search field required"})

        query = " AND ".join(parts)
        papers = await arxiv_client.search(query, max_results, sort_by)
        for p in papers:
            library.add_paper(p)
        return json.dumps({
            "success": True,
            "query": query,
            "count": len(papers),
            "papers": [p.to_dict() for p in papers]
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# === Download & Extract ===

@mcp.tool()
async def arxiv_download_pdf(arxiv_id: str) -> str:
    """Download a paper's PDF to the local library.

    Args:
        arxiv_id: arXiv paper ID (e.g. "2301.07041")

    Returns:
        JSON with file path
    """
    try:
        path = await arxiv_client.download_pdf(arxiv_id)
        library.update_paper(arxiv_id, {"downloaded": True, "pdf_path": path})
        return json.dumps({"success": True, "arxiv_id": arxiv_id, "pdf_path": path})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def arxiv_download_source(arxiv_id: str) -> str:
    """Download a paper's LaTeX source archive.

    Args:
        arxiv_id: arXiv paper ID

    Returns:
        JSON with file path
    """
    try:
        path = await arxiv_client.download_source(arxiv_id)
        library.update_paper(arxiv_id, {"source_path": path})
        return json.dumps({"success": True, "arxiv_id": arxiv_id, "source_path": path})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def arxiv_extract_text(arxiv_id: str) -> str:
    """Extract full text from a downloaded PDF using PyMuPDF.

    Downloads the PDF first if not already downloaded. Caches result.

    Args:
        arxiv_id: arXiv paper ID

    Returns:
        JSON with extracted text
    """
    try:
        paper = library.get_paper(arxiv_id)
        pdf_path = paper.pdf_path if paper and paper.pdf_path else None
        if not pdf_path or not Path(pdf_path).exists():
            pdf_path = await arxiv_client.download_pdf(arxiv_id)
            library.update_paper(arxiv_id, {"downloaded": True, "pdf_path": pdf_path})

        text = pdf_extractor.extract_text(pdf_path)
        return json.dumps({"success": True, "arxiv_id": arxiv_id, "length": len(text), "text": text})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def arxiv_extract_latex(arxiv_id: str) -> str:
    """Unpack LaTeX source and return the main .tex file content.

    Downloads source first if not already downloaded.

    Args:
        arxiv_id: arXiv paper ID

    Returns:
        JSON with raw LaTeX content
    """
    try:
        paper = library.get_paper(arxiv_id)
        source_path = paper.source_path if paper and paper.source_path else None
        if not source_path or not Path(source_path).exists():
            source_path = await arxiv_client.download_source(arxiv_id)
            library.update_paper(arxiv_id, {"source_path": source_path})

        files = latex_extractor.unpack_source(source_path)
        main_tex = latex_extractor.find_main_tex(files)
        if not main_tex:
            return json.dumps({"success": False, "error": "No .tex file found in source"})

        content = Path(main_tex).read_text(encoding="utf-8", errors="ignore")
        return json.dumps({
            "success": True,
            "arxiv_id": arxiv_id,
            "main_file": main_tex,
            "all_files": files,
            "length": len(content),
            "latex": content,
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# === Citation & References ===

@mcp.tool()
async def arxiv_extract_references(arxiv_id: str) -> str:
    """Parse bibliography from a paper's LaTeX source.

    Falls back to PDF text regex if no LaTeX source available.

    Args:
        arxiv_id: arXiv paper ID

    Returns:
        JSON with list of parsed citations
    """
    try:
        import re
        tex_content = None

        # Try LaTeX source first
        paper = library.get_paper(arxiv_id)
        source_path = paper.source_path if paper and paper.source_path else None
        if source_path and Path(source_path).exists():
            files = latex_extractor.unpack_source(source_path)
            main_tex = latex_extractor.find_main_tex(files)
            if main_tex:
                tex_content = Path(main_tex).read_text(encoding="utf-8", errors="ignore")

        if tex_content:
            citations = latex_extractor.extract_references(tex_content)
        else:
            # Fallback: extract from PDF text
            pdf_path = paper.pdf_path if paper and paper.pdf_path else None
            if not pdf_path or not Path(pdf_path).exists():
                pdf_path = await arxiv_client.download_pdf(arxiv_id)
                library.update_paper(arxiv_id, {"downloaded": True, "pdf_path": pdf_path})
            text = pdf_extractor.extract_text(pdf_path)
            # Simple regex for references section
            ref_section = ""
            for marker in ["References", "REFERENCES", "Bibliography"]:
                idx = text.rfind(marker)
                if idx != -1:
                    ref_section = text[idx:]
                    break
            citations = []
            if ref_section:
                lines = [l.strip() for l in ref_section.split("\n") if l.strip()]
                for line in lines[1:]:  # skip header
                    if re.match(r"^\[?\d+\]?", line) or re.match(r"^[A-Z]", line):
                        citations.append(Citation(title=line[:200], authors=[]))

        return json.dumps({
            "success": True,
            "arxiv_id": arxiv_id,
            "count": len(citations),
            "references": [dataclasses.asdict(c) for c in citations],
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def arxiv_citation_graph(arxiv_id: str, limit: int = 50) -> str:
    """Get forward and backward citations via Semantic Scholar.

    Args:
        arxiv_id: arXiv paper ID
        limit: Max citations per direction (default 50)

    Returns:
        JSON with citing_papers and referenced_papers lists
    """
    try:
        citing = await citation_graph.get_citations(arxiv_id, limit)
        referenced = await citation_graph.get_references(arxiv_id, limit)
        return json.dumps({
            "success": True,
            "arxiv_id": arxiv_id,
            "citing_count": len(citing),
            "citing_papers": [dataclasses.asdict(c) for c in citing],
            "referenced_count": len(referenced),
            "referenced_papers": [dataclasses.asdict(c) for c in referenced],
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def arxiv_find_related(arxiv_id: str) -> str:
    """Find related papers via Semantic Scholar recommendations.

    Args:
        arxiv_id: arXiv paper ID

    Returns:
        JSON with recommended papers
    """
    try:
        related = await citation_graph.get_related(arxiv_id)
        return json.dumps({
            "success": True,
            "arxiv_id": arxiv_id,
            "count": len(related),
            "related_papers": [dataclasses.asdict(c) for c in related],
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# === Local Library ===

@mcp.tool()
async def arxiv_list_library(category: str = "", tag: str = "", downloaded_only: bool = False) -> str:
    """List papers in the local library.

    Args:
        category: Filter by arXiv category
        tag: Filter by tag
        downloaded_only: Only show papers with downloaded PDFs

    Returns:
        JSON with paper list
    """
    try:
        papers = library.load_library()
        if category:
            papers = [p for p in papers if category in p.categories]
        if tag:
            papers = [p for p in papers if tag in p.tags]
        if downloaded_only:
            papers = [p for p in papers if p.downloaded]
        return json.dumps({
            "success": True,
            "count": len(papers),
            "papers": [p.to_dict() for p in papers],
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def arxiv_search_library(query: str) -> str:
    """Full-text search across downloaded papers in the library.

    Args:
        query: Search text (case-insensitive substring match)

    Returns:
        JSON with matching papers and context snippets
    """
    try:
        papers = library.load_library()
        results = []
        query_lower = query.lower()
        for p in papers:
            text = p.full_text or ""
            if not text and p.pdf_path and Path(p.pdf_path).exists():
                text = pdf_extractor.extract_text(p.pdf_path)
                library.update_paper(p.arxiv_id, {"full_text": text})
            if query_lower in p.title.lower() or query_lower in p.abstract.lower() or query_lower in text.lower():
                # Find snippet
                snippet = ""
                idx = text.lower().find(query_lower)
                if idx != -1:
                    start = max(0, idx - 100)
                    end = min(len(text), idx + len(query) + 100)
                    snippet = text[start:end]
                results.append({
                    "arxiv_id": p.arxiv_id,
                    "title": p.title,
                    "snippet": snippet,
                })
        return json.dumps({"success": True, "count": len(results), "results": results})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def arxiv_add_note(arxiv_id: str, note: str) -> str:
    """Add or update a note on a paper in the library.

    Args:
        arxiv_id: arXiv paper ID
        note: Note text

    Returns:
        JSON confirmation
    """
    try:
        library.update_paper(arxiv_id, {"notes": note})
        return json.dumps({"success": True, "arxiv_id": arxiv_id, "note": note})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def arxiv_tag_paper(arxiv_id: str, tags: str, remove: bool = False) -> str:
    """Add or remove tags on a paper.

    Args:
        arxiv_id: arXiv paper ID
        tags: Comma-separated tags
        remove: If true, remove these tags instead of adding

    Returns:
        JSON with updated tags
    """
    try:
        paper = library.get_paper(arxiv_id)
        if not paper:
            return json.dumps({"success": False, "error": f"Paper not in library: {arxiv_id}"})

        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        current = list(paper.tags)
        if remove:
            current = [t for t in current if t not in tag_list]
        else:
            for t in tag_list:
                if t not in current:
                    current.append(t)
        library.update_paper(arxiv_id, {"tags": current})
        return json.dumps({"success": True, "arxiv_id": arxiv_id, "tags": current})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# === Reading List ===

@mcp.tool()
async def arxiv_reading_list(priority: int = 0, tag: str = "", unread_only: bool = False) -> str:
    """View the reading list.

    Args:
        priority: Filter by priority (1-5, 0 = all)
        tag: Filter by tag
        unread_only: Only show unread papers

    Returns:
        JSON with reading list entries
    """
    try:
        entries = library.load_reading_list()
        if priority > 0:
            entries = [e for e in entries if e.priority == priority]
        if tag:
            entries = [e for e in entries if tag in e.tags]
        if unread_only:
            entries = [e for e in entries if not e.read]
        return json.dumps({
            "success": True,
            "count": len(entries),
            "entries": [e.to_dict() for e in entries],
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def arxiv_reading_list_manage(
    action: str,
    arxiv_id: str,
    priority: int = 3,
    tags: str = "",
    notes: str = "",
) -> str:
    """Manage the reading list.

    Args:
        action: add, remove, mark_read, mark_unread, update
        arxiv_id: arXiv paper ID
        priority: Priority 1-5 (1=urgent, 5=someday). Used with add/update.
        tags: Comma-separated tags. Used with add/update.
        notes: Notes. Used with add/update.

    Returns:
        JSON confirmation
    """
    try:
        entries = library.load_reading_list()
        existing = next((e for e in entries if e.arxiv_id == arxiv_id), None)

        if action == "add":
            if existing:
                return json.dumps({"success": False, "error": "Already on reading list"})
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            entry = ReadingListEntry(
                arxiv_id=arxiv_id,
                added_at=datetime.now().isoformat(),
                priority=priority,
                tags=tag_list,
                notes=notes,
            )
            entries.append(entry)
            library.update_paper(arxiv_id, {"reading_list": True})

        elif action == "remove":
            entries = [e for e in entries if e.arxiv_id != arxiv_id]
            library.update_paper(arxiv_id, {"reading_list": False})

        elif action == "mark_read":
            if existing:
                existing.read = True

        elif action == "mark_unread":
            if existing:
                existing.read = False

        elif action == "update":
            if existing:
                if priority:
                    existing.priority = priority
                if tags:
                    existing.tags = [t.strip() for t in tags.split(",") if t.strip()]
                if notes:
                    existing.notes = notes
        else:
            return json.dumps({"success": False, "error": f"Unknown action: {action}"})

        library.save_reading_list(entries)
        return json.dumps({"success": True, "action": action, "arxiv_id": arxiv_id})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# === Session Management ===

@mcp.tool()
async def arxiv_session(
    action: str = "current",
    name: str = "",
    session_id: str = "",
    arxiv_id: str = "",
) -> str:
    """Manage research sessions.

    Args:
        action: create, list, current, add_paper, close
        name: Session name (for create)
        session_id: Session ID (for add_paper, close). If empty, uses active session.
        arxiv_id: Paper to add (for add_paper)

    Returns:
        JSON with session data
    """
    try:
        if action == "create":
            if not name:
                return json.dumps({"success": False, "error": "Name required for create"})
            s = session.create_session(name)
            return json.dumps({"success": True, "session": s.to_dict()})

        elif action == "list":
            sessions = session.list_sessions()
            return json.dumps({
                "success": True,
                "count": len(sessions),
                "sessions": [s.to_dict() for s in sessions],
            })

        elif action == "current":
            s = session.get_active_session()
            if not s:
                return json.dumps({"success": True, "session": None, "message": "No active session"})
            return json.dumps({"success": True, "session": s.to_dict()})

        elif action == "add_paper":
            if not arxiv_id:
                return json.dumps({"success": False, "error": "arxiv_id required"})
            sid = session_id or (session.get_active_session() or type("", (), {"session_id": ""})()).session_id
            if not sid:
                return json.dumps({"success": False, "error": "No active session. Create one first."})
            s = session.add_paper_to_session(sid, arxiv_id)
            return json.dumps({"success": True, "session": s.to_dict()})

        elif action == "close":
            sid = session_id or (session.get_active_session() or type("", (), {"session_id": ""})()).session_id
            if not sid:
                return json.dumps({"success": False, "error": "No active session to close"})
            s = session.close_session(sid)
            return json.dumps({"success": True, "session": s.to_dict()})

        else:
            return json.dumps({"success": False, "error": f"Unknown action: {action}"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


if __name__ == "__main__":
    mcp.run()
