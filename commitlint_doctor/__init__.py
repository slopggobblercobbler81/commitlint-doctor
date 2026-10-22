"""commitlint-doctor: Production-grade Conventional Commits validator and git hook enforcer."""

__version__ = "1.0.0"
__author__ = "slopggobblercobbler81"
__all__ = [
    "CommitMessage",
    "CommitParser",
    "Diagnostic",
    "LintReport",
    "Severity",
    "CommitLinter",
    "lint_commit",
    "parse_commit",
]

from .models import CommitMessage, Diagnostic, LintReport, Severity
from .parser import CommitParser, parse_commit
from .linter import CommitLinter, lint_commit
