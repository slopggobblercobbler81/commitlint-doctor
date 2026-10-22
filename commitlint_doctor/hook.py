"""Git hook manager for commitlint-doctor."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Optional, Union

from .linter import CommitLinter
from .models import Severity


HOOK_SIGNATURE = "# commitlint-doctor hook"

HOOK_TEMPLATE = f"""#!/usr/bin/env sh
{HOOK_SIGNATURE}
commitlint-doctor hook check "$1"
"""


def find_git_root(start_dir: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Finds the root .git directory walking upwards from start_dir."""
    curr = Path(start_dir or Path.cwd()).resolve()
    for parent in [curr] + list(curr.parents):
        git_dir = parent / ".git"
        if git_dir.exists():
            return git_dir if git_dir.is_dir() else parent
    return None


def install_hook(
    target_dir: Optional[Union[str, Path]] = None,
    force: bool = False,
) -> Path:
    """Installs the commit-msg git hook."""
    git_dir = find_git_root(target_dir)
    if not git_dir:
        raise FileNotFoundError("Could not locate a .git repository.")

    hooks_dir = git_dir / "hooks" if git_dir.name == ".git" else git_dir / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    hook_file = hooks_dir / "commit-msg"
    if hook_file.exists() and not force:
        content = hook_file.read_text(encoding="utf-8", errors="ignore")
        if HOOK_SIGNATURE not in content:
            raise FileExistsError(
                f"Existing commit-msg hook found at {hook_file}. Use --force to overwrite."
            )

    hook_file.write_text(HOOK_TEMPLATE, encoding="utf-8")

    # Make executable on POSIX systems
    try:
        cur_mode = os.stat(hook_file).st_mode
        os.chmod(hook_file, cur_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except Exception:
        pass

    return hook_file


def uninstall_hook(target_dir: Optional[Union[str, Path]] = None) -> bool:
    """Uninstalls the commit-msg git hook if installed."""
    git_dir = find_git_root(target_dir)
    if not git_dir:
        return False

    hooks_dir = git_dir / "hooks" if git_dir.name == ".git" else git_dir / ".git" / "hooks"
    hook_file = hooks_dir / "commit-msg"

    if not hook_file.exists():
        return False

    content = hook_file.read_text(encoding="utf-8", errors="ignore")
    if HOOK_SIGNATURE in content:
        hook_file.unlink()
        return True

    return False


def check_hook_file(file_path: Union[str, Path], strict: bool = False) -> int:
    """Invoked by git during commit-msg hook execution."""
    p = Path(file_path)
    linter = CommitLinter()
    report = linter.lint_file(p)

    if report.is_valid:
        return 0

    print("\n\033[1;31m[commitlint-doctor] Commit aborted! Non-conventional commit message detected:\033[0m")
    for d in report.errors:
        print(f"  ✗ [{d.rule}] {d.message}")
        if d.suggested_fix:
            print(f"    Suggested fix: {d.suggested_fix}")
    for d in report.warnings:
        print(f"  ⚠ [{d.rule}] {d.message}")

    print("\nSee: https://www.conventionalcommits.org/en/v1.0.0/\n")
    return 1
