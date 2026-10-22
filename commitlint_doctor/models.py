"""Data models for commitlint-doctor."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Diagnostic:
    rule: str
    message: str
    severity: Severity = Severity.ERROR
    line_number: int = 1
    suggested_fix: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule,
            "message": self.message,
            "severity": self.severity.value,
            "line_number": self.line_number,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class CommitFooter:
    token: str
    value: str

    def to_dict(self) -> Dict[str, str]:
        return {"token": self.token, "value": self.value}


@dataclass
class CommitMessage:
    raw: str
    header: str = ""
    commit_type: Optional[str] = None
    scope: Optional[str] = None
    is_breaking: bool = False
    description: Optional[str] = None
    body: Optional[str] = None
    footers: List[CommitFooter] = field(default_factory=list)
    breaking_description: Optional[str] = None
    commit_hash: Optional[str] = None
    author: Optional[str] = None

    @property
    def is_conventional(self) -> bool:
        return bool(self.commit_type and self.description)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header,
            "type": self.commit_type,
            "scope": self.scope,
            "is_breaking": self.is_breaking,
            "description": self.description,
            "body": self.body,
            "footers": [f.to_dict() for f in self.footers],
            "breaking_description": self.breaking_description,
            "commit_hash": self.commit_hash,
            "author": self.author,
        }


@dataclass
class LintReport:
    is_valid: bool
    diagnostics: List[Diagnostic] = field(default_factory=list)
    commit: Optional[CommitMessage] = None

    @property
    def errors(self) -> List[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == Severity.ERROR]

    @property
    def warnings(self) -> List[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == Severity.WARNING]

    @property
    def info(self) -> List[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == Severity.INFO]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "commit": self.commit.to_dict() if self.commit else None,
        }
