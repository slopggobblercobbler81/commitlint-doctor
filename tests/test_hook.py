"""Unit tests for Git commit-msg hook manager."""

import pytest
from commitlint_doctor.hook import (
    HOOK_SIGNATURE,
    check_hook_file,
    find_git_root,
    install_hook,
    uninstall_hook,
)


def test_find_git_root(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    sub = repo / "a" / "b"
    sub.mkdir(parents=True)

    found = find_git_root(sub)
    assert found is not None
    assert found == repo / ".git"


def test_install_and_uninstall_hook(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    hook_path = install_hook(target_dir=repo)
    assert hook_path.exists()
    assert HOOK_SIGNATURE in hook_path.read_text(encoding="utf-8")

    # Install again without force should succeed because signature matches
    install_hook(target_dir=repo, force=False)

    # Uninstall
    assert uninstall_hook(target_dir=repo) is True
    assert not hook_path.exists()
    assert uninstall_hook(target_dir=repo) is False


def test_install_hook_overwriting_foreign_hook(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    hooks = repo / ".git" / "hooks"
    hooks.mkdir(parents=True)
    custom_hook = hooks / "commit-msg"
    custom_hook.write_text("# foreign hook\nexit 0\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        install_hook(target_dir=repo, force=False)

    # With force=True
    install_hook(target_dir=repo, force=True)
    assert HOOK_SIGNATURE in custom_hook.read_text(encoding="utf-8")


def test_check_hook_file(tmp_path, capsys):
    f_valid = tmp_path / "VALID_MSG"
    f_valid.write_text("docs: update README with installation steps\n", encoding="utf-8")
    assert check_hook_file(f_valid) == 0

    f_invalid = tmp_path / "INVALID_MSG"
    f_invalid.write_text("updated readme\n", encoding="utf-8")
    assert check_hook_file(f_invalid) == 1
    out = capsys.readouterr().out
    assert "Commit aborted" in out
