"""Git integration utilities for commit history checking."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple


def get_commits_from_git(
    revision_range: Optional[str] = None,
    last_n: Optional[int] = None,
    cwd: Optional[Path] = None,
) -> List[Tuple[str, str, str]]:
    """Retrieves commits as a list of (commit_hash, author, full_message) tuples.
    
    Format uses ASCII Unit Separator (0x1F) and Record Separator (0x1E).
    """
    cmd = ["git", "log", "--format=%H%x1f%an%x1f%B%x1e"]

    if last_n is not None and last_n > 0:
        cmd.extend(["-n", str(last_n)])
    elif revision_range:
        cmd.append(revision_range)

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            cwd=str(cwd) if cwd else None,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return []

    if proc.returncode != 0 or not proc.stdout.strip():
        return []

    raw_records = proc.stdout.split("\x1e")
    commits: List[Tuple[str, str, str]] = []

    for rec in raw_records:
        rec = rec.strip()
        if not rec:
            continue
        parts = rec.split("\x1f")
        if len(parts) >= 3:
            commit_hash = parts[0].strip()
            author = parts[1].strip()
            message = parts[2].strip()
            commits.append((commit_hash, author, message))

    return commits
