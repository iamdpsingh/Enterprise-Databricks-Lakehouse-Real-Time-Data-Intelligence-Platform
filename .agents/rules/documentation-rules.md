# Documentation as Code Rules

## The Absolute Law
**Nothing gets left undocumented. Documentation is a cross-cutting layer, not an afterthought.**

## 1. Documentation Lifecycle
- All documentation lives in the repository under the `docs/` folder.
- Documentation changes follow the exact same Pull Request and review process as code changes.
- Stale documentation is considered a bug and must be tracked via GitHub Issues.

## 2. Required Documentation Structures
The repository must maintain up-to-date documentation for the following areas. Each area must have a dedicated markdown file.

### Architecture (`docs/architecture/`)
- `system-architecture.md`: High-level system overview.
- `data-architecture.md`: Medallion architecture implementation details.
- `cloud-architecture.md`: GCP infrastructure overview.
- `databricks-architecture.md`: Workspaces, compute, and cluster policies.
- `security-architecture.md`: Threat models, IAM, encryption, and network security.
- `monitoring-architecture.md`: Telemetry, logging, alerting, and observability flow.

### Data (`docs/data/`)
- `data-sources.md`: Up-to-date inventory of all external data sources.
- `data-dictionary.md`: Glossary of business terms and metrics.
- `schemas.md`: Core entities and their relationships.
- `data-contracts.md`: Formal contracts for Gold tier tables.
- `quality-rules.md`: Documentation of every data quality check applied.
- `lineage.md`: Data lineage mapping from source to Gold.

### Pipelines (`docs/pipelines/`)
- `ingestion.md`: How raw data arrives and is processed.
- `batch.md`: Batch processing schedules and dependencies.
- `streaming.md`: Streaming pipelines, watermarking, and SLAs.
- `cdc.md`: Change Data Capture patterns used.
- `transformation.md`: Core transformation logic and business rules.

### Infrastructure (`docs/infrastructure/`)
- `gcp.md`: GCP project structure and resource naming.
- `networking.md`: VPCs, subnets, firewalls, and routing.
- `iam.md`: Roles, groups, and permissions matrix.
- `docker.md`: Base images, container registries, and deployment.
- `terraform.md`: State management, modules, and execution environments.

### Databricks (`docs/databricks/`)
- `workspaces.md`: Workspace topology and configuration.
- `unity-catalog.md`: Metastore, catalogs, schemas, and external locations.
- `delta-lake.md`: Table properties, optimization, and vacuum policies.
- `workflows.md`: Job orchestration, triggers, and dependencies.
- `deployment.md`: Databricks Asset Bundles (DABs) configuration.

### CI/CD (`docs/cicd/`)
- `strategy.md`: Overall deployment philosophy.
- `github-actions.md`: Workflow definitions and triggers.
- `environments.md`: Definition of Dev, Staging, and Prod.
- `release-process.md`: Versioning, changelogs, and release notes.

### Testing (`docs/testing/`)
- `unit-testing.md`: Setup, mocking, and coverage expectations.
- `integration-testing.md`: Cross-service testing approach.
- `data-testing.md`: Data quality testing framework.
- `pipeline-testing.md`: End-to-end pipeline validation.
- `performance-testing.md`: Load testing and benchmarking.

### Monitoring & Operations (`docs/monitoring/` and `docs/operations/`)
- `metrics.md`: Key performance indicators and SLIs.
- `alerts.md`: Alert definitions, thresholds, and routing.
- `dashboards.md`: Overview of the Next.js control center.
- `incident-response.md`: Roles, severity levels, and communication plans.
- `runbook.md`: Standard operating procedures for common tasks.
- `troubleshooting.md`: Known issues and diagnostic steps.
- `disaster-recovery.md`: RTO, RPO, and recovery procedures.
- `rollback.md`: Automated and manual rollback steps.

### Decisions (`docs/decisions/`)
- Architecture Decision Records (ADRs) must be written for all major technical decisions.
- Format: `ADR-001-title.md`
- Template: Context, Options Considered, Decision, Consequences.

## 3. Diagrams as Code
- Architecture diagrams must be version-controlled using tools like Mermaid (e.g., flowcharts, sequence diagrams, ER diagrams, deployment diagrams).
- No proprietary diagram formats (e.g., Visio, Lucidchart) should be the sole source of truth if they cannot be version-controlled in the repository.

## 4. Root Documentation
- `README.md`: Must serve as the entry point, explaining project purpose, setup, and navigation.
- `CHANGELOG.md`: Must be updated for every release using "Keep a Changelog" format.
- `CONTRIBUTING.md`: Guidelines for new developers.
- `SECURITY.md`: Vulnerability reporting process.
