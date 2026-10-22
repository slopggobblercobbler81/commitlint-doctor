"""Unit tests for CommitLinter."""

from commitlint_doctor.linter import CommitLinter, lint_commit, lint_commit_file
from commitlint_doctor.rules import LintConfig


def test_lint_clean_commit():
    text = "feat(auth): support OAuth2 tokens"
    report = lint_commit(text)
    assert report.is_valid
    assert len(report.errors) == 0


def test_lint_empty_commit():
    report = lint_commit("   ")
    assert not report.is_valid
    assert any(d.rule == "commit-empty" for d in report.errors)


def test_lint_strict_escalation():
    text = "feat(AUTH): uppercase scope"
    normal_rep = lint_commit(text, config=LintConfig(strict=False))
    assert normal_rep.is_valid  # scope-case is warning by default

    strict_rep = lint_commit(text, config=LintConfig(strict=True))
    assert not strict_rep.is_valid  # escalated to error in strict mode


def test_lint_file_and_missing_file(tmp_path):
    f = tmp_path / "COMMIT_MSG"
    f.write_text("fix: resolve off-by-one loop index\n", encoding="utf-8")
    report = lint_commit_file(f)
    assert report.is_valid

    missing_rep = lint_commit_file(tmp_path / "does_not_exist")
    assert not missing_rep.is_valid
    assert any(d.rule == "file-not-found" for d in missing_rep.errors)


def test_autofix():
    linter = CommitLinter()
    raw = "FEAT(AUTH): add token refresh.\n\nSome body."
    fixed = linter.autofix(raw)
    assert fixed.startswith("feat(auth): add token refresh")
    assert not fixed.splitlines()[0].endswith(".")
    assert "Some body." in fixed
