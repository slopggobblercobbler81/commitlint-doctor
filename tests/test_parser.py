"""Unit tests for Conventional Commits parser."""

from commitlint_doctor.parser import CommitParser, parse_commit


def test_parse_simple_header():
    msg = parse_commit("feat: add search endpoint")
    assert msg.commit_type == "feat"
    assert msg.scope is None
    assert msg.is_breaking is False
    assert msg.description == "add search endpoint"
    assert msg.is_conventional is True


def test_parse_with_scope():
    msg = parse_commit("fix(auth): resolve jwt expiration bug")
    assert msg.commit_type == "fix"
    assert msg.scope == "auth"
    assert msg.is_breaking is False
    assert msg.description == "resolve jwt expiration bug"


def test_parse_breaking_change_bang():
    msg = parse_commit("feat(db)!: drop legacy v1 schema")
    assert msg.commit_type == "feat"
    assert msg.scope == "db"
    assert msg.is_breaking is True
    assert msg.description == "drop legacy v1 schema"


def test_parse_body_and_footers():
    raw = """feat(cli): add interactive setup wizard

This wizard guides users through initial project configuration,
selecting database drivers and initializing security tokens.

Closes #42
BREAKING CHANGE: old config.ini format is no longer supported.
"""
    msg = parse_commit(raw)
    assert msg.commit_type == "feat"
    assert msg.scope == "cli"
    assert msg.description == "add interactive setup wizard"
    assert msg.body is not None
    assert "This wizard guides users" in msg.body
    assert len(msg.footers) == 2
    assert msg.footers[0].token == "Closes"
    assert msg.footers[0].value == "42"
    assert msg.footers[1].token == "BREAKING CHANGE"
    assert "old config.ini" in msg.footers[1].value
    assert msg.is_breaking is True
    assert msg.breaking_description is not None


def test_parse_git_comments_stripped():
    raw = """fix: handle null pointer

# Please enter the commit message for your changes. Lines starting
# with '#' will be ignored, and an empty message aborts the commit.
# On branch main
"""
    msg = parse_commit(raw, strip_comments=True)
    assert msg.commit_type == "fix"
    assert msg.description == "handle null pointer"
    assert msg.body is None


def test_parse_non_conventional():
    msg = parse_commit("Updated documentation and fixed typo")
    assert msg.commit_type is None
    assert msg.is_conventional is False
    assert msg.header == "Updated documentation and fixed typo"


def test_parse_empty():
    msg = parse_commit("")
    assert msg.header == ""
    assert msg.commit_type is None
    assert msg.is_conventional is False
