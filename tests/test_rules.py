"""Unit tests for individual commitlint rules."""

from commitlint_doctor.models import CommitMessage, Severity
from commitlint_doctor.rules import (
    LintConfig,
    rule_body_leading_blank,
    rule_body_max_line_length,
    rule_header_max_length,
    rule_header_min_length,
    rule_scope_case,
    rule_scope_empty,
    rule_subject_case,
    rule_subject_empty,
    rule_subject_full_stop,
    rule_type_case,
    rule_type_empty,
    rule_type_enum,
)


def test_rule_type_empty():
    cfg = LintConfig()
    msg = CommitMessage(raw="just text", commit_type=None)
    diags = rule_type_empty(msg, cfg)
    assert len(diags) == 1
    assert diags[0].rule == "type-empty"


def test_rule_type_enum():
    cfg = LintConfig()
    bad_msg = CommitMessage(raw="foo: bar", commit_type="foo")
    diags = rule_type_enum(bad_msg, cfg)
    assert len(diags) == 1
    assert diags[0].rule == "type-enum"

    good_msg = CommitMessage(raw="feat: bar", commit_type="feat")
    assert len(rule_type_enum(good_msg, cfg)) == 0


def test_rule_type_case():
    cfg = LintConfig()
    bad_msg = CommitMessage(raw="FEAT: bar", commit_type="FEAT")
    diags = rule_type_case(bad_msg, cfg)
    assert len(diags) == 1
    assert diags[0].rule == "type-case"
    assert diags[0].suggested_fix == "feat"


def test_rule_scope_case():
    cfg = LintConfig()
    bad_msg = CommitMessage(raw="feat(AUTH): bar", scope="AUTH")
    diags = rule_scope_case(bad_msg, cfg)
    assert len(diags) == 1
    assert diags[0].rule == "scope-case"


def test_rule_scope_empty():
    cfg = LintConfig(require_scope=True)
    msg = CommitMessage(raw="feat: bar", commit_type="feat", scope=None)
    diags = rule_scope_empty(msg, cfg)
    assert len(diags) == 1
    assert diags[0].rule == "scope-empty"


def test_rule_subject_empty():
    cfg = LintConfig()
    bad_msg = CommitMessage(raw="feat: ", commit_type="feat", description="")
    diags = rule_subject_empty(bad_msg, cfg)
    assert len(diags) == 1
    assert diags[0].rule == "subject-empty"


def test_rule_subject_full_stop():
    cfg = LintConfig()
    bad_msg = CommitMessage(raw="feat: add thing.", commit_type="feat", description="add thing.")
    diags = rule_subject_full_stop(bad_msg, cfg)
    assert len(diags) == 1
    assert diags[0].rule == "subject-full-stop"
    assert diags[0].suggested_fix == "add thing"


def test_rule_subject_case():
    cfg = LintConfig(enforce_lower_subject=True)
    bad_msg = CommitMessage(raw="feat: Add thing", commit_type="feat", description="Add thing")
    diags = rule_subject_case(bad_msg, cfg)
    assert len(diags) == 1
    assert diags[0].rule == "subject-case"
    assert diags[0].suggested_fix == "add thing"


def test_rule_header_max_length():
    cfg = LintConfig(header_max_length=50)
    long_hdr = "feat: " + "a" * 60
    msg = CommitMessage(raw=long_hdr, header=long_hdr)
    diags = rule_header_max_length(msg, cfg)
    assert len(diags) == 1
    assert diags[0].rule == "header-max-length"


def test_rule_header_min_length():
    cfg = LintConfig(header_min_length=10)
    msg = CommitMessage(raw="feat: a", header="feat: a")
    diags = rule_header_min_length(msg, cfg)
    assert len(diags) == 1
    assert diags[0].rule == "header-min-length"


def test_rule_body_leading_blank():
    cfg = LintConfig()
    no_blank = CommitMessage(raw="feat: something\nline immediately below without blank line")
    diags = rule_body_leading_blank(no_blank, cfg)
    assert len(diags) == 1
    assert diags[0].rule == "body-leading-blank"


def test_rule_body_max_line_length():
    cfg = LintConfig(body_max_line_length=40)
    long_body = "This is a very long line in the commit body that exceeds forty characters easily."
    msg = CommitMessage(raw="feat: ok", body=long_body)
    diags = rule_body_max_line_length(msg, cfg)
    assert len(diags) == 1
    assert diags[0].rule == "body-max-line-length"
