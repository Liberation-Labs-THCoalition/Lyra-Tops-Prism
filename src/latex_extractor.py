"""LaTeX source extraction and bibliography parsing."""

import tarfile
import gzip
import os
import re
from pathlib import Path
from typing import Optional
from models import Citation


def unpack_source(archive_path: str) -> list[str]:
    """Unpack a LaTeX source archive (.tar.gz or .gz).

    Args:
        archive_path: Path to the source archive

    Returns:
        List of extracted file paths
    """
    archive_path = Path(archive_path)
    dest_dir = archive_path.parent / "source"
    dest_dir.mkdir(parents=True, exist_ok=True)

    extracted_files = []

    try:
        # Try as tar.gz first
        with tarfile.open(str(archive_path), "r:gz") as tar:
            tar.extractall(path=str(dest_dir))
            extracted_files = [str(dest_dir / m.name) for m in tar.getmembers() if m.isfile()]
    except tarfile.TarError:
        # Try as plain gzip (single .tex file)
        try:
            out_path = dest_dir / "main.tex"
            with gzip.open(str(archive_path), "rb") as f_in:
                content = f_in.read()
            out_path.write_bytes(content)
            extracted_files = [str(out_path)]
        except Exception:
            raise ValueError(f"Could not unpack archive: {archive_path}")

    return extracted_files


def find_main_tex(tex_files: list[str]) -> Optional[str]:
    """Find the main .tex file in a list of extracted files.

    Heuristic: look for \\documentclass or \\begin{document}.
    Prefer files named main.tex, paper.tex, or the one with \\documentclass.
    """
    tex_only = [f for f in tex_files if f.endswith(".tex")]

    if not tex_only:
        return None

    if len(tex_only) == 1:
        return tex_only[0]

    # Prefer common main file names
    for name in ["main.tex", "paper.tex", "manuscript.tex", "article.tex"]:
        for f in tex_only:
            if Path(f).name.lower() == name:
                return f

    # Look for \documentclass
    for f in tex_only:
        try:
            content = Path(f).read_text(encoding="utf-8", errors="ignore")
            if "\\documentclass" in content:
                return f
        except Exception:
            continue

    return tex_only[0]


def extract_references(tex_content: str) -> list[Citation]:
    """Parse bibliography entries from LaTeX content.

    Handles:
    - \\bibitem entries in thebibliography environment
    - BibTeX-style entries if .bib content is inline

    Args:
        tex_content: Raw LaTeX source

    Returns:
        List of Citation objects
    """
    citations = []

    # Pattern 1: \bibitem{key} content
    bibitem_pattern = r"\\bibitem(?:\[.*?\])?\{(.*?)\}\s*(.*?)(?=\\bibitem|\\end\{thebibliography\})"
    matches = re.findall(bibitem_pattern, tex_content, re.DOTALL)

    for key, content in matches:
        content = _clean_latex(content.strip())
        citation = _parse_citation_text(content)
        citations.append(citation)

    # Pattern 2: BibTeX @article{key, ...} style
    bibtex_pattern = r"@\w+\{(.*?),\s*(.*?)\n\}"
    bib_matches = re.findall(bibtex_pattern, tex_content, re.DOTALL)

    for key, fields_text in bib_matches:
        citation = _parse_bibtex_entry(fields_text)
        citations.append(citation)

    return citations


def _clean_latex(text: str) -> str:
    """Remove common LaTeX commands from text."""
    # Remove \textit{}, \textbf{}, \emph{} keeping content
    text = re.sub(r"\\(?:textit|textbf|emph|text)\{(.*?)\}", r"\1", text)
    # Remove \cite{...}
    text = re.sub(r"\\cite\{.*?\}", "", text)
    # Remove remaining backslash commands
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    # Clean up braces
    text = text.replace("{", "").replace("}", "")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_citation_text(text: str) -> Citation:
    """Best-effort parse of a bibliography entry text."""
    # Try to extract authors (before first period or comma-heavy section)
    parts = text.split(".", 1)
    authors_text = parts[0] if len(parts) > 1 else ""
    title_text = parts[1].strip().split(".")[0] if len(parts) > 1 else text.split(".")[0]

    # Extract year
    year_match = re.search(r"\b(19|20)\d{2}\b", text)
    year = int(year_match.group()) if year_match else 0

    # Extract arXiv ID
    arxiv_match = re.search(r"(\d{4}\.\d{4,5})", text)
    arxiv_id = arxiv_match.group(1) if arxiv_match else ""

    # Extract DOI
    doi_match = re.search(r"(10\.\d{4,}/\S+)", text)
    doi = doi_match.group(1) if doi_match else ""

    authors = [a.strip() for a in authors_text.split(",") if a.strip()] if authors_text else []

    return Citation(
        title=title_text.strip(),
        authors=authors[:10],  # Cap at 10
        arxiv_id=arxiv_id,
        doi=doi,
        year=year,
    )


def _parse_bibtex_entry(fields_text: str) -> Citation:
    """Parse BibTeX fields into a Citation."""
    def get_field(name: str) -> str:
        match = re.search(rf"{name}\s*=\s*\{{(.*?)\}}", fields_text, re.DOTALL)
        return match.group(1).strip() if match else ""

    title = get_field("title")
    author_str = get_field("author")
    year_str = get_field("year")
    doi = get_field("doi")

    authors = [a.strip() for a in author_str.replace(" and ", ",").split(",") if a.strip()]
    year = int(year_str) if year_str.isdigit() else 0

    arxiv_match = re.search(r"(\d{4}\.\d{4,5})", fields_text)
    arxiv_id = arxiv_match.group(1) if arxiv_match else ""

    return Citation(
        title=_clean_latex(title),
        authors=authors[:10],
        arxiv_id=arxiv_id,
        doi=doi,
        year=year,
    )
