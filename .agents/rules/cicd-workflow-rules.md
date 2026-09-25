# CI/CD Workflow Rules

## The Absolute Laws
1. **Nothing goes directly from a developer laptop to production. Ever.**
2. **Every code, configuration, infrastructure, notebook, schema, and documentation change is version-controlled in Git.**
3. **Every production deployment goes through GitHub CI/CD.**
4. **No manual interventions in production unless declared an incident and documented.**

---

## 1. Branching Strategy

### Branch Types
| Branch | Purpose | Protected? | Requires PR? |
|--------|---------|-----------|--------------|
| `main` | Production-ready source of truth | Yes | Yes |
| `staging` | Staging environment source | Yes | Yes |
| `develop` | Integration branch for features | Yes | Yes |
| `feature/<name>` | Individual feature development | No | Yes (to develop) |
| `fix/<name>` | Bug fixes | No | Yes |
| `hotfix/<name>` | Emergency production fixes | No | Yes (to main) |
| `chore/<name>` | Refactoring, tooling, config | No | Yes |
| `docs/<name>` | Documentation-only changes | No | Yes |
| `infra/<name>` | Terraform/infrastructure changes | No | Yes |

### Naming Conventions
- Branch names must be lowercase and hyphen-separated.
- Branch names must be descriptive: `feature/auto-loader-bronze-ingestion`, not `feature/fix1`.
- Maximum branch lifetime: 7 days for features, 2 days for hotfixes.
- Stale branches older than 14 days must be deleted.

### Branch Protection Rules (enforce in GitHub settings)
- `main`, `staging`, `develop` require:
  - At least 1 approving PR review
  - All CI status checks passing
  - Branches must be up-to-date before merging
  - No force pushes
  - No branch deletions
  - Conversation threads must be resolved

---

## 2. Pull Request Rules

### When to Open a PR
- Open a PR as soon as the branch has meaningful commits — **Draft PRs are encouraged** for early feedback.
- Convert to Ready for Review only when all local tests pass.

### PR Requirements Before Merge
Every PR must include:
- [ ] A descriptive title using the format: `[type] short description` (e.g., `[feat] Add Auto Loader Bronze ingestion for CSV sources`)
- [ ] Filled-out PR description from the PR template
- [ ] Link to the GitHub Issue it addresses
- [ ] All CI checks passing (zero failures tolerated)
- [ ] At least 1 approving review
- [ ] No unresolved review comments
- [ ] Self-review completed by the author

### PR Template (`.github/pull_request_template.md`)
Every PR must have:
- Summary of change
- Type of change (feature / fix / refactor / docs / infra / chore)
- Linked issues
- How to test / verify the change
- What was NOT changed (scope boundaries)
- Checklist: tests added, docs updated, security considered, data quality impact assessed

### PR Size Guidelines
- Keep PRs small and focused. Prefer multiple small PRs over one giant PR.
- If a PR touches more than 600 lines of code, it must be justified in the description.

---

## 3. Continuous Integration (CI) — Required Gates

CI must run automatically on every PR and every push to `develop`, `staging`, and `main`.

### Python / PySpark
- `ruff check .` — linting (zero errors)
- `ruff format --check .` — formatting (zero violations)
- `mypy src/` — type checking (zero errors on strict mode)
- `pytest tests/unit/` — unit tests (100% pass, ≥80% coverage)
- `pytest tests/integration/` — integration tests (100% pass)
- `pytest tests/data_quality/` — data quality tests (100% pass)

### SQL
- SQL linting via `sqlfluff lint` (configurable rules)
- SQL formatting check via `sqlfluff format --check`

### TypeScript / Next.js
- `tsc --noEmit` — TypeScript type checking (zero errors)
- `eslint .` — ESLint (zero errors)
- `prettier --check .` — formatting (zero violations)
- `npm run test` — Jest unit tests (100% pass)
- `npm run build` — production build must succeed

### Docker
- `docker build` must succeed for all Dockerfiles
- Docker image security scan (Trivy or Grype — zero critical/high vulnerabilities)
- Image size must not exceed a defined threshold

### Infrastructure
- `terraform validate` for all Terraform modules
- `terraform plan` must succeed (no destructive changes on protected environments without explicit approval)
- `tflint` — linting (zero errors)

### Security
- `bandit -r src/` — Python security scan (zero high-severity findings)
- `pip-audit` — dependency vulnerability scan
- `npm audit --audit-level=high` — Node.js dependency scan
- Secret scanning via `trufflehog` or GitHub's built-in secret scanning

### Documentation
- All Markdown files must pass `markdownlint`
- Mermaid diagrams must be valid (syntax checked)
- All ADR files must follow the required template structure

---

## 4. Continuous Deployment (CD) — Pipeline Stages

### Stage 1: Development Deployment
- Trigger: Merge to `develop`
- Target: Development environment (Databricks Dev workspace + GCP Dev project)
- Steps:
  1. Build artifacts (Python packages, Docker images, Databricks bundles)
  2. Push Docker images to GCP Artifact Registry (dev tag)
  3. Deploy Databricks Asset Bundles to dev workspace
  4. Run post-deployment smoke tests
  5. Post Slack/notification with deployment status

### Stage 2: Staging Deployment
- Trigger: Merge to `staging` (or manual promotion from `develop`)
- Target: Staging environment
- Steps:
  1. All steps from Stage 1 (with staging configs)
  2. Run full integration test suite against staging environment
  3. Run data quality validation on staging data
  4. Run performance baseline tests
  5. Require explicit approval gate before proceeding to production

### Stage 3: Production Deployment
- Trigger: Merge to `main` + manual approval gate (at least 1 approver)
- Target: Production environment
- Steps:
  1. Deploy with blue/green or rolling strategy where applicable
  2. Run post-deployment validation suite
  3. Verify pipeline health metrics in monitoring dashboard
  4. Create GitHub Release with auto-generated changelog
  5. Notify stakeholders of successful deployment
  6. Tag the deployed commit: `v{major}.{minor}.{patch}`

---

## 5. Environment Configuration Rules

- **Never hardcode environment-specific values** (project IDs, workspace URLs, catalog names, schema names).
- All configurations must be loaded from:
  - `configs/{env}/config.yaml` — non-sensitive configuration
  - GCP Secret Manager — all sensitive values (credentials, connection strings, API keys)
  - GitHub Actions Environment Secrets — CI/CD-specific secrets
- Environment-specific resources must have environment prefixes/suffixes (e.g., `catalog_dev`, `catalog_prod`).

---

## 6. Hotfix Process

For critical production bugs only:
1. Create branch: `hotfix/description` from `main`
2. Fix must be minimal — only address the critical issue
3. Open PR against `main`
4. Hotfix CI must pass all checks
5. Requires at minimum 1 emergency reviewer approval
6. After merge to `main`, immediately back-merge into `develop` and `staging`
7. Create a post-incident document in `docs/operations/incidents/`

---

## 7. Rollback Rules

- Every deployment must have a documented rollback procedure in `docs/operations/rollback.md`.
- Rollback must be automated (re-run previous GitHub Actions deployment with prior artifact tags).
- Rollback must complete within 15 minutes for critical failures.
- After any rollback, an incident report must be created within 24 hours.

---

## 8. Release Management

- Use semantic versioning: `MAJOR.MINOR.PATCH`
  - **MAJOR**: Breaking changes to API/schema/pipeline contracts
  - **MINOR**: New features or significant enhancements (backward-compatible)
  - **PATCH**: Bug fixes, performance improvements (backward-compatible)
- `CHANGELOG.md` must be updated on every release using Keep a Changelog format.
- GitHub Releases must be created for every production deployment with full release notes.

---

## 9. CI/CD Governance

- All workflow YAML files in `.github/workflows/` must be version-controlled.
- Changes to CI/CD workflows themselves require a PR review.
- CI secrets must never be echoed in logs — use GitHub's masked secrets.
- CI pipelines must have timeout limits to prevent runaway jobs:
  - Lint/check jobs: 5 minutes
  - Unit test jobs: 10 minutes
  - Integration test jobs: 30 minutes
  - Build jobs: 20 minutes
  - Deployment jobs: 45 minutes

---

## 10. CODEOWNERS

`.github/CODEOWNERS` must be maintained to ensure the right people review the right changes:
- `databricks/` → data engineers
- `infrastructure/` → infrastructure/DevOps
- `monitoring-ui/` → frontend developers
- `src/` → data engineers
- `.github/workflows/` → DevOps lead (required review)
- `docs/` → all contributors (any reviewer)
- `SECURITY.md` → security lead (required review)
