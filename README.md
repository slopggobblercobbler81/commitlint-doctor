# commitlint-doctor 🩺📜

[![CI](https://github.com/slopggobblercobbler81/commitlint-doctor/actions/workflows/ci.yml/badge.svg)](https://github.com/slopggobblercobbler81/commitlint-doctor/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Conventional Commits 1.0.0](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](https://github.com/slopggobblercobbler81/commitlint-doctor)

**commitlint-doctor** is a production-grade, zero-dependency developer CLI utility and Python library to validate, enforce, and autofix [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) specifications across git hooks, PR workflows, and commit history.

Designed for high-speed local git hooks and CI/CD pipelines without requiring Node.js or heavy npm dependencies.

---

## 🚀 Key Features

- 🎯 **Full Conventional Commits 1.0.0 Compliance**:
  - Validates `<type>[optional scope][!]: <description>`.
  - Supports standard types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
  - Validates breaking change indicators (`!` in header and `BREAKING CHANGE:` / `BREAKING-CHANGE:` footers).
  - Validates footer references (`Closes #123`, `Fixes #456`, `Refs`, `Co-authored-by`).
- 🪝 **Built-in Native Git Hook Manager**:
  - One-click install and uninstall of `.git/hooks/commit-msg`.
  - Enforces commit rules before commits are finalized.
- 🔍 **Git History & PR Branch Scanner (`check-range`)**:
  - Scan commit history ranges (e.g. `main..HEAD`) or the last N commits (`--last 10`).
  - Perfect for GitHub Actions pull request validation.
- ⚡ **Zero External Dependencies**: Pure Python standard library, instant execution for sub-millisecond hook responsiveness.
- 🛠️ **Smart Autofix (`fix`)**: Automatically normalizes uppercase types/scopes and strips trailing periods from commit subjects.
- 📊 **Machine-Readable JSON Output**: Integrates into dashboards and custom CI pipelines with `--json`.

---

## 📦 Installation

```bash
pip install commitlint-doctor
```

Or install from source:
```bash
git clone https://github.com/slopggobblercobbler81/commitlint-doctor.git
cd commitlint-doctor
pip install -e .
```

---

## 🛠️ Usage Guide

### 1. Lint Single Commit Message
Lint an inline commit message:
```bash
commitlint-doctor check -m "feat(auth): add OAuth2 refresh token handling"
```

Lint a commit message file (e.g. from git hook):
```bash
commitlint-doctor check -f .git/COMMIT_EDITMSG
```

Lint from stdin:
```bash
echo "fix: memory leak in worker pool" | commitlint-doctor check
```

Output machine-readable JSON:
```bash
commitlint-doctor check -m "feat: new feature" --json
```

### 2. Enforce Strict or Custom Rules
Require explicit scopes:
```bash
commitlint-doctor check -m "feat: missing scope" --require-scope
```

Define custom allowed types:
```bash
commitlint-doctor check -m "deploy: update k8s manifests" --types feat,fix,deploy,infra
```

Fail on any warnings (strict mode):
```bash
commitlint-doctor check -m "feat(UI): bad casing" --strict
```

### 3. Scan Git History & PR Branches
Scan all commits between `main` and current branch:
```bash
commitlint-doctor check-range main..HEAD
```

Scan the last 5 commits:
```bash
commitlint-doctor check-range --last 5
```

### 4. Git `commit-msg` Hook Management
Install native git hook:
```bash
commitlint-doctor hook install
```

Uninstall git hook:
```bash
commitlint-doctor hook uninstall
```

### 5. Autofix Non-Compliant Commits
Automatically correct minor syntax issues (type casing, trailing period):
```bash
commitlint-doctor fix -m "FEAT(AUTH): add token support."
# Output: feat(auth): add token support

# Fix a file directly
commitlint-doctor fix -f .git/COMMIT_EDITMSG -w
```

---

## 🤖 Pre-commit Integration

Add to `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/slopggobblercobbler81/commitlint-doctor
    rev: v1.0.0
    hooks:
      - id: commitlint-doctor
        name: Lint Commit Message
        entry: commitlint-doctor check -f
        language: python
        stages: [commit-msg]
```

---

## 🧪 Running Tests

```bash
pytest -v
```

All 30+ unit tests cover parser, rules, linter, git hook manager, history scanner, and CLI commands.

---

## 📄 License

MIT © [slopggobblercobbler81](https://github.com/slopggobblercobbler81)
