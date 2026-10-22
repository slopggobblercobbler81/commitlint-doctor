"""Core linter implementation for Conventional Commits."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from .models import CommitMessage, Diagnostic, LintReport, Severity
from .parser import CommitParser
from .rules import ALL_RULES, LintConfig


class CommitLinter:
    """Linter that evaluates commit messages against conventional rules."""

    def __init__(self, config: Optional[LintConfig] = None):
        self.config = config or LintConfig()

    def lint_text(self, text: str) -> LintReport:
        commit = CommitParser.parse(text)
        diagnostics: List[Diagnostic] = []

        if not text.strip():
            diagnostics.append(
                Diagnostic(
                    rule="commit-empty",
                    message="Commit message is empty.",
                    severity=Severity.ERROR,
                    line_number=1,
                )
            )
            return LintReport(is_valid=False, diagnostics=diagnostics, commit=commit)

        for rule in ALL_RULES:
            rule_diags = rule(commit, self.config)
            diagnostics.extend(rule_diags)

        # Strict mode escalation
        if self.config.strict:
            for d in diagnostics:
                if d.severity == Severity.WARNING:
                    d.severity = Severity.ERROR

        is_valid = not any(d.severity == Severity.ERROR for d in diagnostics)
        diagnostics.sort(key=lambda d: d.line_number)

        return LintReport(
            is_valid=is_valid,
            diagnostics=diagnostics,
            commit=commit,
        )

    def lint_file(self, path: Union[str, Path]) -> LintReport:
        p = Path(path)
        if not p.exists():
            return LintReport(
                is_valid=False,
                diagnostics=[
                    Diagnostic(
                        rule="file-not-found",
                        message=f"Commit file not found: {p}",
                        severity=Severity.ERROR,
                        line_number=1,
                    )
                ],
                commit=None,
            )
        text = p.read_text(encoding="utf-8", errors="replace")
        return self.lint_text(text)

    def autofix(self, text: str) -> str:
        """Attempts to automatically fix common non-compliant formatting."""
        commit = CommitParser.parse(text)
        if not commit.commit_type or not commit.description:
            return text

        fixed_type = commit.commit_type.lower()
        fixed_scope = commit.scope.lower() if commit.scope else None
        fixed_desc = commit.description.rstrip().rstrip(".")

        breaking_mark = "!" if commit.is_breaking else ""
        if fixed_scope:
            header = f"{fixed_type}({fixed_scope}){breaking_mark}: {fixed_desc}"
        else:
            header = f"{fixed_type}{breaking_mark}: {fixed_desc}"

        lines = [header]
        if commit.body:
            lines.append("")
            lines.append(commit.body)

        if commit.footers:
            lines.append("")
            for f in commit.footers:
                lines.append(f"{f.token}: {f.value}")

        return "\n".join(lines)


def lint_commit(text: str, config: Optional[LintConfig] = None) -> LintReport:
    return CommitLinter(config=config).lint_text(text)


def lint_commit_file(path: Union[str, Path], config: Optional[LintConfig] = None) -> LintReport:
    return CommitLinter(config=config).lint_file(path)
