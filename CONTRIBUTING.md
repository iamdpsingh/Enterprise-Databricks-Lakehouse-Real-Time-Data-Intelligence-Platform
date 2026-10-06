# Contributing to Enterprise Databricks Lakehouse Platform

Thank you for contributing! This document explains the standards, workflow, and expectations for all contributors.

---

## 🔰 Development Prerequisites

Before contributing, ensure you have:
- Python 3.10+
- Node.js 20+
- Git with GPG signing configured
- `pre-commit` installed and hooks activated (`pre-commit install`)
- Access to the Development Databricks workspace (request via GitHub Issue)

---

## 🌿 Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production — never commit directly |
| `staging` | Pre-production validation |
| `develop` | Integration branch for features |
| `feature/<id>-desc` | Your feature work |
| `bugfix/<id>-desc` | Bug fixes |
| `hotfix/<id>-desc` | Emergency production fixes |
| `docs/<desc>` | Documentation-only changes |
| `infra/<desc>` | Infrastructure / Terraform changes |

**Always branch from `develop`. Never commit directly to `main` or `staging`.**

---

## 📋 Pull Request Process

1. Create a GitHub Issue for your work first.
2. Create a branch: `git checkout -b feature/DE-123-add-bronze-ingestion`
3. Make atomic commits (one logical change per commit).
4. Open a PR against `develop` using the PR template.
5. All CI checks must pass before requesting review.
6. At least 1 approval required before merging.
7. Squash merging is **not** used — keep individual commits.

---

## ✍️ Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body — explain WHY>

Closes #<issue-number>
```

**Types:** `feat`, `fix`, `docs`, `test`, `ci`, `infra`, `chore`, `ref`, `perf`

**Examples:**
```
feat(ingestion): Add Auto Loader Bronze ingestion for Salesforce CSV exports

Implements cloudFiles-based incremental ingestion from the GCS landing zone.
Adds mandatory metadata columns (_metadata_batch_id, _metadata_source_system, etc.)
and schema evolution handling in rescue mode.

Closes #42
```

---

## 🧪 Testing Requirements

- All new code in `src/` must have corresponding unit tests in `tests/unit/`.
- Minimum code coverage: **85%** (enforced in CI).
- Tests must pass locally before opening a PR: `pytest tests/unit/ -v`
- Tests must be marked with the correct pytest marker (`@pytest.mark.unit`, `@pytest.mark.integration`).

---

## 🎨 Code Style

All style is automatically enforced via pre-commit hooks. Run manually:
```bash
ruff check . --fix        # Fix linting issues
ruff format .             # Format code
mypy src/                 # Type check
sqlfluff lint --dialect sparksql sql/  # Lint SQL
```

---

## 📖 Documentation

- Every new feature must update the relevant documentation in `docs/`.
- New architectural decisions require an ADR in `ADR/`.
- Every new Gold table requires a data contract in `data-contracts/`.

---

## 🔒 Security

- **Never commit secrets, credentials, or API keys.** Use GCP Secret Manager.
- `detect-secrets` runs as a pre-commit hook. If it triggers, investigate before bypassing.
- Report security vulnerabilities via [SECURITY.md](./SECURITY.md) — do NOT open a public issue.
