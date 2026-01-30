# arXiv MCP Server

Full-featured arXiv research pipeline as an MCP server. Search papers, download PDFs + LaTeX source, extract full text, parse citations, explore citation graphs, and manage a local paper library.

## Setup

1. **Install dependencies:**
   ```bash
   cd arxiv-mcp
   python -m venv .venv
   source .venv/Scripts/activate  # Windows/Git Bash
   pip install -r requirements.txt
   ```

2. **Configure (optional):**
   ```bash
   cp .env.example .env
   # Edit .env if you want custom storage dir or Semantic Scholar API key
   ```

3. **Register in Claude Code:**
   Add to `claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "arxiv": {
         "command": "C:/Users/Thomas/Desktop/LiberationLabs/Agent+ Design/arxiv-mcp/.venv/Scripts/python.exe",
         "args": ["C:/Users/Thomas/Desktop/LiberationLabs/Agent+ Design/arxiv-mcp/src/server.py"]
       }
     }
   }
   ```

## Tools (18)

### Search & Discovery
- `arxiv_search` — Search with query string (supports ti:, au:, abs:, cat: syntax)
- `arxiv_get_paper` — Get metadata by arXiv ID
- `arxiv_browse_category` — Recent papers in a category
- `arxiv_advanced_search` — Field-specific search params

### Download & Extract
- `arxiv_download_pdf` — Download PDF locally
- `arxiv_download_source` — Download LaTeX source archive
- `arxiv_extract_text` — Full text from PDF (PyMuPDF, cached)
- `arxiv_extract_latex` — Unpack and read .tex source

### Citation & References
- `arxiv_extract_references` — Parse bibliography from LaTeX/PDF
- `arxiv_citation_graph` — Forward + backward citations (Semantic Scholar)
- `arxiv_find_related` — Recommended similar papers

### Local Library
- `arxiv_list_library` — List papers with filters
- `arxiv_search_library` — Full-text search across downloaded papers
- `arxiv_add_note` — Annotate papers
- `arxiv_tag_paper` — Tag papers

### Reading List
- `arxiv_reading_list` — View with priority/tag/read filters
- `arxiv_reading_list_manage` — Add, remove, mark read, update

### Session
- `arxiv_session` — Create/list/current/add_paper/close research sessions

## Storage

Papers and metadata stored at `~/.arxiv-mcp/` (configurable via `ARXIV_DATA_DIR`).

## Dependencies

- `mcp` — MCP framework
- `arxiv` — arXiv API client
- `httpx` — Async HTTP (Semantic Scholar)
- `PyMuPDF` — PDF text extraction
