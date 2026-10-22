"""Parser for Conventional Commits."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from .models import CommitFooter, CommitMessage


HEADER_REGEX = re.compile(
    r"^([a-zA-Z0-9_-]+)(?:\(([^\r\n()]+)\))?(!)?:\s*(.*)$"
)

FOOTER_REGEX = re.compile(
    r"^(BREAKING CHANGE|BREAKING-CHANGE|[a-zA-Z0-9_-]+)(?::\s*|\s+#)(.*)$"
)


class CommitParser:
    """Parses raw git commit messages into structured CommitMessage objects."""

    @classmethod
    def clean_message(cls, raw: str, strip_comments: bool = True) -> str:
        lines = raw.splitlines()
        cleaned: List[str] = []
        for line in lines:
            if strip_comments and line.strip().startswith("#"):
                continue
            cleaned.append(line)
        # Strip trailing blank lines
        while cleaned and not cleaned[-1].strip():
            cleaned.pop()
        return "\n".join(cleaned)

    @classmethod
    def parse(cls, raw: str, strip_comments: bool = True) -> CommitMessage:
        cleaned_text = cls.clean_message(raw, strip_comments=strip_comments)
        lines = cleaned_text.splitlines()

        if not lines:
            return CommitMessage(raw=raw, header="")

        header = lines[0].strip()
        body_lines: List[str] = []
        footers: List[CommitFooter] = []
        breaking_desc: Optional[str] = None

        commit_type: Optional[str] = None
        scope: Optional[str] = None
        is_breaking: bool = False
        description: Optional[str] = None

        m = HEADER_REGEX.match(header)
        if m:
            commit_type = m.group(1)
            scope = m.group(2)
            is_breaking = bool(m.group(3))
            description = m.group(4)

        if len(lines) > 1:
            remaining_lines = lines[1:]

            # Parse footers from bottom upwards if they match footer syntax
            footer_idx = len(remaining_lines)
            for i in range(len(remaining_lines) - 1, -1, -1):
                cur_line = remaining_lines[i].strip()
                if not cur_line:
                    # Blank line marks separation
                    continue
                f_match = FOOTER_REGEX.match(cur_line)
                if f_match:
                    token = f_match.group(1)
                    val = f_match.group(2).strip()
                    footers.insert(0, CommitFooter(token=token, value=val))
                    if token in ("BREAKING CHANGE", "BREAKING-CHANGE"):
                        is_breaking = True
                        breaking_desc = val
                    footer_idx = i
                else:
                    break

            # The lines between header and footers form the body
            potential_body = remaining_lines[:footer_idx]
            body_text = "\n".join(potential_body).strip()
            if body_text:
                body_lines.append(body_text)

        body_str = "\n".join(body_lines).strip() if body_lines else None

        return CommitMessage(
            raw=raw,
            header=header,
            commit_type=commit_type,
            scope=scope,
            is_breaking=is_breaking,
            description=description,
            body=body_str,
            footers=footers,
            breaking_description=breaking_desc,
        )


def parse_commit(raw: str, strip_comments: bool = True) -> CommitMessage:
    return CommitParser.parse(raw, strip_comments=strip_comments)
