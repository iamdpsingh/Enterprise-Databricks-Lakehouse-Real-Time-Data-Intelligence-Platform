# Repository Structure & Project Workflow Rules

## 1. The Repository is the Single Source of Truth
Every artifact that matters — code, configuration, infrastructure, documentation, data contracts, schemas, and CI/CD pipelines — lives in this repository. If it is not in Git, it does not exist officially.

---

## 2. Canonical Directory Structure

The repository must maintain this exact directory layout. Every new component must be placed in the correct location. Do not create ad-hoc directories at the root level without an ADR justifying the deviation.

```
project-6-databricks-lakehouse/
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                    # Main CI gate — runs on every PR
│   │   ├── cd-dev.yml                # CD to Development environment
│   │   ├── cd-staging.yml            # CD to Staging environment
│   │   ├── cd-prod.yml               # CD to Production environment
│   │   ├── docker.yml                # Build, scan, and push Docker images
│   │   └── documentation.yml         # Validate and publish docs
│   ├── CODEOWNERS                    # Code ownership mapping
│   ├── pull_request_template.md      # Standard PR checklist
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       ├── feature_request.md
│       └── data_quality_incident.md
│
├── databricks/
│   ├── notebooks/                    # Exploratory notebooks (NOT production code)
│   ├── pipelines/                    # Lakeflow / DLT pipeline definitions
│   ├── workflows/                    # Databricks Workflow YAML job definitions
│   ├── sql/                          # SQL scripts for UC grants, maintenance, views
│   ├── schemas/                      # Table schema definitions (JSON/YAML)
│   └── resources/                    # databricks.yml (Asset Bundle root config)
│
├── src/
│   ├── ingestion/                    # Auto Loader, API, and file ingestion modules
│   ├── transformations/              # Bronze → Silver → Gold transformation logic
│   ├── streaming/                    # Structured Streaming job definitions
│   ├── cdc/                          # Change Data Capture merge patterns
│   ├── quality/                      # Data quality validation framework
│   └── utilities/                    # Shared helpers: logging, config, retry, etc.
│
├── sql/
│   ├── bronze/                       # DDL for Bronze tables
│   ├── silver/                       # DDL for Silver tables
│   └── gold/                         # DDL for Gold tables / views
│
├── tests/
│   ├── unit/                         # Fast, mocked, no-cluster tests
│   ├── integration/                  # Tests against real Dev environment
│   ├── data_quality/                 # Data expectation / contract tests
│   └── performance/                  # Benchmark and SLA validation tests
│
├── infrastructure/
│   ├── terraform/
│   │   ├── modules/                  # Reusable Terraform modules
│   │   ├── envs/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── prod/
│   │   └── variables.tf
│   ├── docker/                       # Dockerfiles and compose files
│   └── gcp/                          # GCP-specific configs (bucket policies, IAM)
│
├── monitoring/
│   ├── metrics/                      # Metric definitions and collection configs
│   ├── alerts/                       # Alert rules and routing configs
│   └── dashboards/                   # JSON dashboard definitions
│
├── monitoring-ui/                    # Next.js Data Platform Control Center
│   ├── src/
│   │   ├── app/                      # Next.js App Router pages
│   │   ├── components/               # Reusable React components
│   │   ├── lib/                      # API clients, utilities
│   │   └── types/                    # TypeScript type definitions
│   ├── package.json
│   └── tsconfig.json
│
├── scripts/                          # Utility scripts (setup, data seeding, etc.)
├── configs/                          # Environment-specific non-secret configuration
│   ├── dev/
│   ├── staging/
│   └── prod/
├── data-contracts/                   # Formal data contracts for Gold tables
├── docs/                             # All project documentation
├── ADR/                              # Architecture Decision Records
├── notebooks/                        # Shared exploratory notebooks (non-production)
│
├── pyproject.toml                    # Python project definition, deps, and tooling config
├── .pre-commit-config.yaml           # Pre-commit hook definitions
├── .markdownlint.json                # Markdown lint configuration
├── .sqlfluff                         # SQL formatting rules
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
└── CHANGELOG.md
```

---

## 3. File Placement Rules

- **Production Python code** belongs in `src/`. Never write ETL logic inside notebooks for production pipelines.
- **Notebooks** in `databricks/notebooks/` or `notebooks/` are for exploration and prototyping only. Code graduates from notebook to `src/` module before being considered production.
- **Terraform** modules must be organized by environment (`envs/dev`, `envs/staging`, `envs/prod`). Shared logic must be extracted into reusable `modules/`.
- **Configurations** that differ per environment belong in `configs/{env}/`. Shared/static config belongs in `configs/common/`.
- **Data contracts** for every Gold table belong in `data-contracts/` as YAML files.
- **ADRs** (Architecture Decision Records) are numbered sequentially: `ADR/ADR-001-use-delta-lake.md`.

---

## 4. Commit Strategy — Atomic Commits for Contribution Count

Every meaningful unit of work must be a separate, focused commit. Never bundle unrelated changes into a single commit. This ensures:
- A clean, readable Git history.
- Easy bisection for debugging.
- Maximum contribution activity on GitHub.

### What constitutes a separate commit:
- Adding a new Python module in `src/` → 1 commit.
- Writing the corresponding unit tests → 1 commit.
- Adding a new Terraform resource → 1 commit.
- Creating or updating a documentation file → 1 commit.
- Adding or modifying a GitHub Actions workflow → 1 commit.
- Writing a new SQL table DDL → 1 commit.
- Creating a new data contract YAML → 1 commit.

### Commit message format (Conventional Commits):
```
<type>(<scope>): <subject>

<body — explain WHY, not what>

<footer: issue refs, co-authors>
```

Types: `feat`, `fix`, `docs`, `test`, `ci`, `infra`, `chore`, `ref`, `perf`, `style`

Examples:
- `feat(ingestion): Add Auto Loader Bronze ingestion for CSV sales data`
- `test(quality): Add unit tests for null check validator`
- `docs(architecture): Add Mermaid sequence diagram for CDC flow`
- `ci(github-actions): Add Python lint gate to CI workflow`
- `infra(terraform): Add GCS bucket for raw data landing zone`

---

## 5. Issue-Driven Development

- Every non-trivial piece of work must have a corresponding GitHub Issue before starting.
- Issues must be linked to PRs via keywords: `Closes #<issue-number>`.
- Use GitHub Projects to track work across the board.
- Issue labels must be maintained: `bug`, `feature`, `documentation`, `infrastructure`, `data-quality`, `security`, `performance`.

---

## 6. Weekly Contribution Rhythm

To maintain a healthy and consistent contribution graph:
- Documentation updates and ADR writing count as real commits — do them.
- Refactoring existing code into proper modules is a commit.
- Adding type hints and docstrings to existing functions is a commit.
- Every new data quality rule written = 1 commit.
- Every new schema file added = 1 commit.
