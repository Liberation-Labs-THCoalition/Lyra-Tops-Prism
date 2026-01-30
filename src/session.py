"""Research session management."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import config
from models import ResearchSession


def _sessions_dir() -> Path:
    config.ensure_dirs()
    return config.SESSIONS_DIR


def create_session(name: str) -> ResearchSession:
    """Create a new research session."""
    session = ResearchSession(
        session_id=str(uuid.uuid4())[:8],
        name=name,
        created_at=datetime.now().isoformat(),
    )
    _save_session(session)
    return session


def list_sessions() -> list[ResearchSession]:
    """List all sessions."""
    sessions = []
    for f in _sessions_dir().glob("session_*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sessions.append(ResearchSession.from_dict(data))
        except Exception:
            continue
    return sorted(sessions, key=lambda s: s.created_at, reverse=True)


def get_session(session_id: str) -> Optional[ResearchSession]:
    """Get a session by ID."""
    path = _sessions_dir() / f"session_{session_id}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return ResearchSession.from_dict(data)


def get_active_session() -> Optional[ResearchSession]:
    """Get the current active session (most recent active one)."""
    sessions = [s for s in list_sessions() if s.active]
    return sessions[0] if sessions else None


def add_paper_to_session(session_id: str, arxiv_id: str) -> ResearchSession:
    """Add a paper to a session."""
    session = get_session(session_id)
    if not session:
        raise ValueError(f"Session not found: {session_id}")
    if arxiv_id not in session.papers:
        session.papers.append(arxiv_id)
    _save_session(session)
    return session


def close_session(session_id: str) -> ResearchSession:
    """Close a session."""
    session = get_session(session_id)
    if not session:
        raise ValueError(f"Session not found: {session_id}")
    session.active = False
    _save_session(session)
    return session


def _save_session(session: ResearchSession):
    """Persist session to disk."""
    config.ensure_dirs()
    path = _sessions_dir() / f"session_{session.session_id}.json"
    path.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")
