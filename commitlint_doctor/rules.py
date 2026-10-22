"""Validation rules for commitlint-doctor."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set

from .models import CommitMessage, Diagnostic, Severity


DEFAULT_TYPES: Set[str] = {
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
}


class LintConfig:
    """Configuration for commitlint rules."""

    def __init__(
        self,
        allowed_types: Optional[Set[str]] = None,
        header_max_length: int = 72,
        header_min_length: int = 5,
        body_max_line_length: int = 100,
        enforce_lower_subject: bool = False,
        require_scope: bool = False,
        strict: bool = False,
    ):
        self.allowed_types = allowed_types or DEFAULT_TYPES
        self.header_max_length = header_max_length
        self.header_min_length = header_min_length
        self.body_max_line_length = body_max_line_length
        self.enforce_lower_subject = enforce_lower_subject
        self.require_scope = require_scope
        self.strict = strict


RuleValidator = Callable[[CommitMessage, LintConfig], List[Diagnostic]]


def rule_type_empty(msg: CommitMessage, config: LintConfig) -> List[Diagnostic]:
    if not msg.commit_type:
        return [
            Diagnostic(
                rule="type-empty",
                message="Commit type is missing or malformed (expected '<type>[optional-scope]: <description>').",
                severity=Severity.ERROR,
                line_number=1,
                suggested_fix="feat: <description>",
            )
        ]
    return []


def rule_type_enum(msg: CommitMessage, config: LintConfig) -> List[Diagnostic]:
    if msg.commit_type and msg.commit_type.lower() not in {t.lower() for t in config.allowed_types}:
        valid = ", ".join(sorted(config.allowed_types))
        return [
            Diagnostic(
                rule="type-enum",
                message=f"Commit type '{msg.commit_type}' is not allowed. Must be one of: {valid}.",
                severity=Severity.ERROR,
                line_number=1,
            )
        ]
    return []


def rule_type_case(msg: CommitMessage, config: LintConfig) -> List[Diagnostic]:
    if msg.commit_type and not msg.commit_type.islower():
        return [
            Diagnostic(
                rule="type-case",
                message=f"Commit type '{msg.commit_type}' must be in lowercase.",
                severity=Severity.ERROR,
                line_number=1,
                suggested_fix=msg.commit_type.lower(),
            )
        ]
    return []


def rule_scope_case(msg: CommitMessage, config: LintConfig) -> List[Diagnostic]:
    if msg.scope and not msg.scope.islower():
        return [
            Diagnostic(
                rule="scope-case",
                message=f"Scope '{msg.scope}' must be in lowercase.",
                severity=Severity.WARNING,
                line_number=1,
                suggested_fix=msg.scope.lower(),
            )
        ]
    return []


def rule_scope_empty(msg: CommitMessage, config: LintConfig) -> List[Diagnostic]:
    if config.require_scope and not msg.scope:
        return [
            Diagnostic(
                rule="scope-empty",
                message="Commit scope is required but was not provided.",
                severity=Severity.ERROR,
                line_number=1,
                suggested_fix=f"{msg.commit_type or 'feat'}(scope): {msg.description or 'description'}",
            )
        ]
    return []


def rule_subject_empty(msg: CommitMessage, config: LintConfig) -> List[Diagnostic]:
    if msg.commit_type and (not msg.description or not msg.description.strip()):
        return [
            Diagnostic(
                rule="subject-empty",
                message="Commit description/subject cannot be empty.",
                severity=Severity.ERROR,
                line_number=1,
            )
        ]
    return []


def rule_subject_full_stop(msg: CommitMessage, config: LintConfig) -> List[Diagnostic]:
    if msg.description and msg.description.rstrip().endswith("."):
        clean_desc = msg.description.rstrip().rstrip(".")
        return [
            Diagnostic(
                rule="subject-full-stop",
                message="Commit subject must not end with a period/full-stop ('.').",
                severity=Severity.ERROR,
                line_number=1,
                suggested_fix=clean_desc,
            )
        ]
    return []


def rule_subject_case(msg: CommitMessage, config: LintConfig) -> List[Diagnostic]:
    if msg.description and config.enforce_lower_subject:
        first_char = msg.description.strip()[:1]
        if first_char.isupper():
            lowered = first_char.lower() + msg.description.strip()[1:]
            return [
                Diagnostic(
                    rule="subject-case",
                    message="Commit subject should start with a lowercase letter.",
                    severity=Severity.WARNING,
                    line_number=1,
                    suggested_fix=lowered,
                )
            ]
    return []


def rule_header_max_length(msg: CommitMessage, config: LintConfig) -> List[Diagnostic]:
    if len(msg.header) > config.header_max_length:
        return [
            Diagnostic(
                rule="header-max-length",
                message=f"Commit header length ({len(msg.header)} chars) exceeds maximum allowed ({config.header_max_length} chars).",
                severity=Severity.WARNING if not config.strict else Severity.ERROR,
                line_number=1,
            )
        ]
    return []


def rule_header_min_length(msg: CommitMessage, config: LintConfig) -> List[Diagnostic]:
    if msg.header and len(msg.header) < config.header_min_length:
        return [
            Diagnostic(
                rule="header-min-length",
                message=f"Commit header length ({len(msg.header)} chars) is shorter than minimum required ({config.header_min_length} chars).",
                severity=Severity.ERROR,
                line_number=1,
            )
        ]
    return []


def rule_body_leading_blank(msg: CommitMessage, config: LintConfig) -> List[Diagnostic]:
    raw_lines = msg.raw.splitlines()
    if len(raw_lines) >= 2:
        # Line 0 is header, line 1 must be empty if there is subsequent body/footer
        if raw_lines[1].strip() != "" and not raw_lines[1].strip().startswith("#"):
            return [
                Diagnostic(
                    rule="body-leading-blank",
                    message="A blank line must separate the commit header from the body.",
                    severity=Severity.WARNING if not config.strict else Severity.ERROR,
                    line_number=2,
                )
            ]
    return []


def rule_body_max_line_length(msg: CommitMessage, config: LintConfig) -> List[Diagnostic]:
    diags: List[Diagnostic] = []
    if msg.body:
        for idx, line in enumerate(msg.body.splitlines()):
            # Ignore markdown link defs or URLs
            if len(line) > config.body_max_line_length and not line.strip().startswith("http") and not line.strip().startswith("["):
                diags.append(
                    Diagnostic(
                        rule="body-max-line-length",
                        message=f"Body line exceeds maximum length ({len(line)} > {config.body_max_line_length} chars).",
                        severity=Severity.WARNING,
                        line_number=idx + 3,
                    )
                )
    return diags


ALL_RULES: List[RuleValidator] = [
    rule_type_empty,
    rule_type_enum,
    rule_type_case,
    rule_scope_case,
    rule_scope_empty,
    rule_subject_empty,
    rule_subject_full_stop,
    rule_subject_case,
    rule_header_max_length,
    rule_header_min_length,
    rule_body_leading_blank,
    rule_body_max_line_length,
]
