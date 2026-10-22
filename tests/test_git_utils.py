"""Unit tests for Git utilities."""

import subprocess
from commitlint_doctor.cli import main
from commitlint_doctor.git_utils import get_commits_from_git


def test_get_commits_from_git_and_cli_scan(tmp_path):
    repo = tmp_path / "test_repo"
    repo.mkdir()

    # Initialize a git repo and make commits
    subprocess.run(["git", "init", "-b", "main"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=str(repo), check=True)

    f1 = repo / "file1.txt"
    f1.write_text("hello", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "feat(init): first commit"], cwd=str(repo), check=True, capture_output=True)

    f2 = repo / "file2.txt"
    f2.write_text("world", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "docs: add documentation"], cwd=str(repo), check=True, capture_output=True)

    commits = get_commits_from_git(last_n=2, cwd=repo)
    assert len(commits) == 2
    assert "docs: add documentation" in commits[0][2]
    assert "feat(init): first commit" in commits[1][2]
