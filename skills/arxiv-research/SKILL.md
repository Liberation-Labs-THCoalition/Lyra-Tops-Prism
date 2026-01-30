---
name: arxiv-research
description: Research workflow using arXiv MCP tools for academic paper discovery, reading, citation exploration, and session management.
---

# arXiv Research Workflow

## When to Use
- Searching for academic papers on a topic
- Building a literature review
- Exploring citation networks
- Reading and annotating papers
- Managing a research reading queue

## Discovery

### Basic Search
Use `arxiv_search` with a natural language query or arXiv syntax (ti:, au:, abs:, cat:, all: with AND/OR/ANDNOT).

### Field-Specific Search
Use `arxiv_advanced_search` with separate title, author, abstract, and category params.

### Category Browsing
Use `arxiv_browse_category` for recent papers in a field (e.g. cs.AI, cs.CL, math.CO).

### Quick Lookup
Use `arxiv_get_paper` with a known arXiv ID for instant metadata.

## Deep Reading

1. **Download**: `arxiv_download_pdf` to get the PDF locally
2. **Extract Text**: `arxiv_extract_text` for full text (cached after first extraction)
3. **LaTeX Source**: `arxiv_download_source` + `arxiv_extract_latex` for raw LaTeX
4. **References**: `arxiv_extract_references` to parse the bibliography
5. **Annotate**: `arxiv_add_note` and `arxiv_tag_paper` to capture insights

## Citation Exploration

- `arxiv_citation_graph` — forward citations (who cites this?) and backward (what does this cite?)
- `arxiv_find_related` — Semantic Scholar's recommended similar papers

## Reading List

- `arxiv_reading_list_manage action="add"` — add papers with priority (1=urgent, 5=someday) and tags
- `arxiv_reading_list` — view filtered by priority, tag, or read status
- `arxiv_reading_list_manage action="mark_read"` — mark as read when done

## Session Management

Create named sessions to track papers you're actively working with:
- `arxiv_session action="create" name="attention mechanisms survey"`
- `arxiv_session action="add_paper" arxiv_id="2301.07041"`
- `arxiv_session action="current"` — view active session
- `arxiv_session action="close"` — close when done

## Library Management

- `arxiv_list_library` — all papers, filtered by category/tag/download status
- `arxiv_search_library` — full-text search across all downloaded papers

## Common Patterns

### Literature Review
1. `arxiv_search` broad topic → triage abstracts
2. `arxiv_browse_category` for recent work
3. Add top papers to reading list with priorities
4. Download + extract text for deep reading
5. `arxiv_citation_graph` on seminal papers for network mapping
6. `arxiv_search_library` for cross-cutting themes

### Paper Deep Dive
1. `arxiv_get_paper` for metadata
2. `arxiv_extract_text` for full content
3. Discuss with AI
4. `arxiv_extract_references` to map bibliography
5. `arxiv_citation_graph` for field context
6. `arxiv_add_note` to record insights
