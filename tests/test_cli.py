"""Unit tests for commitlint-doctor CLI."""

import json
from commitlint_doctor.cli import main


def test_cli_version(capsys):
    try:
        main(["--version"])
    except SystemExit:
        pass
    out = capsys.readouterr().out
    assert "commitlint-doctor" in out


def test_cli_check_valid_string(capsys):
    ret = main(["check", "-m", "feat(cli): add check command"])
    assert ret == 0
    out = capsys.readouterr().out
    assert "complies" in out


def test_cli_check_invalid_string(capsys):
    ret = main(["check", "-m", "random commit without conventional structure"])
    assert ret == 1
    out = capsys.readouterr().out
    assert "validation failed" in out.lower()


def test_cli_check_json_output(capsys):
    ret = main(["check", "-m", "fix: resolve memory leak", "--json"])
    assert ret == 0
    data = json.loads(capsys.readouterr().out)
    assert data["is_valid"] is True
    assert data["commit"]["type"] == "fix"


def test_cli_check_file(tmp_path, capsys):
    f = tmp_path / "msg.txt"
    f.write_text("refactor: extract parser helpers\n", encoding="utf-8")
    ret = main(["check", "-f", str(f)])
    assert ret == 0


def test_cli_check_custom_types(capsys):
    # 'deploy' is not standard
    assert main(["check", "-m", "deploy: release to prod"]) == 1

    # allowed with --types
    assert main(["check", "-m", "deploy: release to prod", "--types", "feat,fix,deploy"]) == 0


def test_cli_check_require_scope(capsys):
    assert main(["check", "-m", "feat: missing scope", "--require-scope"]) == 1
    assert main(["check", "-m", "feat(scope): valid scope", "--require-scope"]) == 0


def test_cli_fix_command(tmp_path, capsys):
    ret = main(["fix", "-m", "FIX(CORE): bad casing."])
    assert ret == 0
    out = capsys.readouterr().out
    assert "fix(core): bad casing" in out

    f = tmp_path / "fixme.txt"
    f.write_text("DOCS(CLI): wrong case.\n", encoding="utf-8")
    ret_w = main(["fix", "-f", str(f), "-w"])
    assert ret_w == 0
    assert "docs(cli): wrong case" in f.read_text(encoding="utf-8")


def test_cli_no_args(capsys):
    ret = main([])
    assert ret == 0
