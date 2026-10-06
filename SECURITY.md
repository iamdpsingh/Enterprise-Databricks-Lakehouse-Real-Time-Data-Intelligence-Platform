# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main` | ✅ |
| `staging` | ✅ |
| Other branches | ❌ |

---

## Reporting a Vulnerability

**Please do NOT open a public GitHub Issue for security vulnerabilities.**

Report vulnerabilities privately via one of these channels:
- **GitHub Private Vulnerability Reporting** (preferred): Go to the repository → Security tab → "Report a vulnerability".
- **GitHub Discussion (Private)**: Use GitHub's private vulnerability reporting — go to the repository → Security tab → "Report a vulnerability" (this is the only supported reporting channel for this project).

### What to Include in Your Report
- Description of the vulnerability and potential impact.
- Steps to reproduce the issue.
- Affected component (GCP, Databricks, GitHub Actions, Next.js, Python code).
- Any suggested fix or mitigation if known.

### What to Expect
- **Acknowledgment** within 48 hours.
- **Initial assessment** within 5 business days.
- **Fix timeline** communicated based on severity (P1: 24h, P2: 7 days, P3: 30 days).
- You will be credited in the security advisory unless you prefer to remain anonymous.

---

## Security Architecture

This platform enforces defense-in-depth:

- **GitHub**: Branch protection, secret scanning, dependency review on every PR.
- **CI/CD**: SAST (Bandit), dependency audit (pip-audit), container scanning (Trivy).
- **GCP**: IAM with least privilege, Workload Identity Federation (no static keys), VPC isolation, Secret Manager.
- **Databricks**: Unity Catalog data governance, row/column level security, audit logging.
- **Code**: No hardcoded credentials, pre-commit secret detection, regular dependency updates.

---

## Dependency Management

- Python dependencies are reviewed via `pip-audit` on every CI run.
- Node.js dependencies are reviewed via `npm audit` on every CI run.
- Critical CVEs block the CI pipeline and must be resolved before merging.

---

## Credential & Secret Policy

- No credentials, API keys, or tokens may be committed to this repository.
- All secrets are stored in GCP Secret Manager.
- GitHub Actions authenticate to GCP via Workload Identity Federation (no JSON keys).
- Databricks service principals use OAuth M2M authentication.
