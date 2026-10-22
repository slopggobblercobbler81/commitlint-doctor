"""Command line interface for commitlint-doctor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .git_utils import get_commits_from_git
from .hook import check_hook_file, install_hook, uninstall_hook
from .linter import CommitLinter
from .models import Severity
from .rules import LintConfig


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="commitlint-doctor",
        description="Production-grade Conventional Commits validator, git hook enforcer, and commit history linter.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: check / lint
    check_p = subparsers.add_parser(
        "check",
        aliases=["lint", "validate"],
        help="Lint a single commit message string, file, or stdin.",
    )
    check_p.add_argument(
        "-m",
        "--message",
        help="Commit message string to lint.",
    )
    check_p.add_argument(
        "-f",
        "--file",
        help="Path to file containing commit message (e.g. .git/COMMIT_EDITMSG).",
    )
    check_p.add_argument(
        "--strict",
        action="store_true",
        help="Escalate style and formatting warnings into fatal errors.",
    )
    check_p.add_argument(
        "--types",
        help="Comma-separated list of allowed commit types (e.g. feat,fix,docs).",
    )
    check_p.add_argument(
        "--require-scope",
        action="store_true",
        help="Enforce that all commit messages must specify a scope.",
    )
    check_p.add_argument(
        "--max-header-length",
        type=int,
        default=72,
        help="Maximum header length in characters (default: 72).",
    )
    check_p.add_argument(
        "--json",
        action="store_true",
        help="Output diagnostics in JSON format.",
    )

    # Command: check-range / scan
    scan_p = subparsers.add_parser(
        "check-range",
        aliases=["scan", "log"],
        help="Lint a range of commits in git history or PR branch.",
    )
    scan_p.add_argument(
        "revision_range",
        nargs="?",
        default=None,
        help="Git revision range to inspect (e.g. 'main..HEAD' or 'HEAD~5..HEAD').",
    )
    scan_p.add_argument(
        "--last",
        type=int,
        default=None,
        help="Lint the last N commits in the current branch.",
    )
    scan_p.add_argument(
        "--strict",
        action="store_true",
        help="Escalate warnings to errors.",
    )
    scan_p.add_argument(
        "--json",
        action="store_true",
        help="Output report in JSON format.",
    )

    # Command: hook
    hook_p = subparsers.add_parser(
        "hook",
        help="Manage git commit-msg hooks.",
    )
    hook_sub = hook_p.add_subparsers(dest="hook_action", help="Hook actions")

    hook_install = hook_sub.add_parser("install", help="Install git commit-msg hook.")
    hook_install.add_argument("--force", action="store_true", help="Overwrite existing hook.")

    hook_sub.add_parser("uninstall", help="Uninstall git commit-msg hook.")

    hook_check = hook_sub.add_parser("check", help="Internal hook check runner.")
    hook_check.add_argument("file", help="Path to commit message file.")

    # Command: fix
    fix_p = subparsers.add_parser(
        "fix",
        help="Autofix formatting on a commit message (lowercase type/scope, remove trailing dot).",
    )
    fix_p.add_argument("-m", "--message", help="Commit message to autofix.")
    fix_p.add_argument("-f", "--file", help="Commit message file to fix.")
    fix_p.add_argument("-w", "--write", action="store_true", help="Write changes directly to file.")

    return parser


def build_config(args: argparse.Namespace) -> LintConfig:
    types = None
    if getattr(args, "types", None):
        types = {t.strip() for t in args.types.split(",") if t.strip()}

    return LintConfig(
        allowed_types=types,
        header_max_length=getattr(args, "max_header_length", 72),
        require_scope=getattr(args, "require_scope", False),
        strict=getattr(args, "strict", False),
    )


def handle_check(args: argparse.Namespace) -> int:
    text: Optional[str] = None

    if args.message is not None:
        text = args.message
    elif args.file:
        p = Path(args.file)
        if not p.exists():
            print(f"Error: Commit message file '{args.file}' does not exist.", file=sys.stderr)
            return 1
        text = p.read_text(encoding="utf-8", errors="replace")
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        print("Error: No commit message provided. Use -m, -f, or pass via stdin.", file=sys.stderr)
        return 1

    config = build_config(args)
    linter = CommitLinter(config=config)
    report = linter.lint_text(text)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.is_valid else 1

    if report.is_valid and not report.diagnostics:
        print("✓ Commit message complies with Conventional Commits 1.0.0!")
        return 0

    if report.is_valid:
        print("✓ Valid commit message with non-fatal recommendations:")
        for d in report.diagnostics:
            icon = "⚠" if d.severity == Severity.WARNING else "ℹ"
            print(f"  {icon} line {d.line_number}: [{d.rule}] {d.message}")
            if d.suggested_fix:
                print(f"    Suggested fix: {d.suggested_fix}")
        return 0

    print(f"✗ Conventional Commit validation failed with {len(report.errors)} error(s):")
    for d in report.errors:
        print(f"  ✗ line {d.line_number}: [{d.rule}] {d.message}")
        if d.suggested_fix:
            print(f"    Suggested fix: {d.suggested_fix}")
    for d in report.warnings:
        print(f"  ⚠ line {d.line_number}: [{d.rule}] {d.message}")

    return 1


def handle_scan(args: argparse.Namespace) -> int:
    config = build_config(args)
    linter = CommitLinter(config=config)

    commits = get_commits_from_git(
        revision_range=args.revision_range,
        last_n=args.last,
    )

    if not commits:
        if args.json:
            print(json.dumps({"total_checked": 0, "failures": 0, "reports": []}, indent=2))
        else:
            print("No git commits found in specified range.")
        return 0

    results: List[dict] = []
    has_failure = False

    if not args.json:
        print(f"Scanning {len(commits)} commit(s) in git history...")

    for commit_hash, author, message in commits:
        short_hash = commit_hash[:8]
        report = linter.lint_text(message)
        if report.commit:
            report.commit.commit_hash = short_hash
            report.commit.author = author

        results.append({
            "hash": short_hash,
            "author": author,
            "report": report.to_dict(),
        })

        if not report.is_valid:
            has_failure = True
            if not args.json:
                print(f"\n  ✗ Commit {short_hash} by {author}:")
                for d in report.errors:
                    print(f"    ✗ [{d.rule}] {d.message}")
        else:
            if not args.json:
                print(f"  ✓ {short_hash}: {message.splitlines()[0][:60]}")

    if args.json:
        print(json.dumps({
            "total_checked": len(commits),
            "failures": sum(1 for r in results if not r["report"]["is_valid"]),
            "commits": results,
        }, indent=2))
        return 1 if has_failure else 0

    if has_failure:
        print("\n✗ Commit range validation failed.")
        return 1

    print(f"\n✓ All {len(commits)} commits are compliant!")
    return 0


def handle_hook(args: argparse.Namespace) -> int:
    if args.hook_action == "install":
        try:
            path = install_hook(force=args.force)
            print(f"✓ Git commit-msg hook installed successfully to: {path}")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    elif args.hook_action == "uninstall":
        success = uninstall_hook()
        if success:
            print("✓ Git commit-msg hook uninstalled.")
        else:
            print("Notice: No commitlint-doctor hook was found to uninstall.")
        return 0
    elif args.hook_action == "check":
        return check_hook_file(args.file)
    else:
        print("Use 'commitlint-doctor hook --help' for available actions.", file=sys.stderr)
        return 1


def handle_fix(args: argparse.Namespace) -> int:
    text: Optional[str] = None
    file_path: Optional[Path] = None

    if args.message:
        text = args.message
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File '{args.file}' does not exist.", file=sys.stderr)
            return 1
        text = file_path.read_text(encoding="utf-8")
    else:
        print("Error: Provide -m or -f to fix.", file=sys.stderr)
        return 1

    linter = CommitLinter()
    fixed = linter.autofix(text)

    if file_path and args.write:
        file_path.write_text(fixed, encoding="utf-8")
        print(f"✓ Autofixed {file_path}")
    else:
        print(fixed)

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command in ("check", "lint", "validate"):
        return handle_check(args)
    elif args.command in ("check-range", "scan", "log"):
        return handle_scan(args)
    elif args.command == "hook":
        return handle_hook(args)
    elif args.command == "fix":
        return handle_fix(args)

    return 0
