# Security & Governance — Full Implementation Specification

## 1. The Defense-in-Depth Model
Security is not a single gate. It is enforced at every layer:
1. **Developer Machine** — pre-commit secret scanning, no credentials in code.
2. **GitHub** — branch protection, secret scanning, dependency review.
3. **CI/CD** — SAST scanning (Bandit), dependency audit (pip-audit), DAST on staging.
4. **GCP** — IAM, VPC, Secret Manager, Cloud Audit Logs, Cloud Armor.
5. **Databricks** — Unity Catalog permissions, service principals, audit logs.
6. **Data** — row/column level security, PII masking, data classification.

---

## 2. Identity & Access Management (IAM) — GCP

### Principle of Least Privilege
No service account, user, or role should have more permissions than strictly required for its function. Permissions must be reviewed and reduced whenever a workload changes.

### Service Account Naming Convention
```
sa-<function>-<env>@<project-id>.iam.gserviceaccount.com

Examples:
sa-databricks-runner-dev@project-lakehouse-dev.iam.gserviceaccount.com
sa-github-ci-deployer-prod@project-lakehouse-prod.iam.gserviceaccount.com
sa-nextjs-api-reader-prod@project-lakehouse-prod.iam.gserviceaccount.com
```

### Forbidden Practices
- ❌ Never use `roles/owner` or `roles/editor` bindings for service accounts.
- ❌ Never download service account JSON keys. Use Workload Identity Federation.
- ❌ Never grant `allUsers` or `allAuthenticatedUsers` access to any resource.
- ❌ Never use default Compute Engine service accounts for production workloads.

### Workload Identity Federation for GitHub Actions
GitHub Actions authenticates to GCP without any static credentials:
```yaml
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: 'projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
    service_account: 'sa-github-ci-deployer-prod@project-id.iam.gserviceaccount.com'
```

---

## 3. Secrets Management — Zero Hardcoded Credentials

### Hierarchy of Secrets Storage
1. **GCP Secret Manager** — the primary vault for all application secrets.
2. **GitHub Actions Secrets (Environment-scoped)** — for CI/CD pipeline authentication values.
3. **Databricks Secret Scopes** — backed by GCP Secret Manager, for use within notebooks and jobs.

### What Must Be in Secret Manager (not in code, not in configs)
- Database connection strings.
- External API keys (Stripe, Salesforce, external data vendors).
- Databricks personal access tokens (for local development only — never in production code).
- GCP service account keys (if legacy systems force JSON key use).
- JWT signing secrets.

### Secret Access Pattern in Python
```python
from google.cloud import secretmanager

def get_secret(project_id: str, secret_name: str, version: str = "latest") -> str:
    """Retrieve a secret value from GCP Secret Manager.

    Args:
        project_id: The GCP project ID where the secret is stored.
        secret_name: The name of the secret (without the full resource path).
        version: The version of the secret to retrieve.

    Returns:
        The decoded secret value as a string.
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/{version}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```

### Secret Rotation
- All secrets must have a maximum lifetime of 90 days.
- Secret rotation must be automated where possible.
- Databricks tokens must be rotated on every production deployment via CD.

---

## 4. Network Security

### VPC Architecture
- Deploy Databricks workspaces in a customer-managed VPC with Private Google Access enabled.
- Use VPC Service Controls to define a security perimeter around sensitive GCP resources.
- Cloud NAT provides outbound internet access for private instances without exposing them.
- All inter-service communication must happen via Private Service Connect or internal VPC routing.

### Firewall Rules
- Default deny all ingress.
- Allow ingress only on specific ports from specific source ranges.
- Allow egress only to known destination CIDRs (Databricks control plane, GCP APIs).
- No SSH open to `0.0.0.0/0`.

---

## 5. Unity Catalog — Data Governance Model

### The Access Control Hierarchy
```
Metastore (1 per region)
  └── Catalog (1 per environment: dev_catalog, prod_catalog)
        ├── bronze (schema)
        │     └── Tables: READ by ingestion SPs only
        ├── silver (schema)
        │     └── Tables: READ by transformation SPs, WRITE by ingestion SPs
        ├── gold (schema)
        │     └── Tables: READ by BI tools, Next.js API SA, Power BI SA
        └── quarantine (schema)
              └── Tables: READ/WRITE by data engineering team SPs only
```

### Row-Level Security (Dynamic Data Masking)
For tables containing PII (Personally Identifiable Information):
```sql
-- Create a row filter for territory-based access
CREATE FUNCTION silver.row_filter_by_territory(territory_code STRING)
RETURN is_member('data_team_global') OR current_user() LIKE CONCAT('%@', territory_code, '.company.com');

ALTER TABLE silver.customers
SET ROW FILTER silver.row_filter_by_territory ON (territory_code);
```

### Column Masking for PII
```sql
-- Mask email addresses for non-PII authorized users
CREATE FUNCTION silver.mask_email(email STRING)
RETURN CASE
    WHEN is_member('pii_authorized') THEN email
    ELSE CONCAT(LEFT(email, 2), '****@****.com')
END;

ALTER TABLE silver.customers
ALTER COLUMN email SET MASK silver.mask_email;
```

### Data Classification Tags
Every table and column containing sensitive data must be tagged in Unity Catalog:
```sql
ALTER TABLE silver.customers
SET TAGS ('pii' = 'true', 'classification' = 'confidential', 'data_owner' = 'data-engineering');

ALTER TABLE silver.customers
ALTER COLUMN email SET TAGS ('pii_type' = 'email', 'masked' = 'true');
```

---

## 6. Container Security (Docker)

- All Docker base images must use pinned SHA256 digests, not tags:
  ```dockerfile
  # BAD
  FROM python:3.11-slim

  # GOOD
  FROM python:3.11-slim@sha256:abc123...
  ```
- Run all containers as non-root users:
  ```dockerfile
  RUN addgroup --system appgroup && adduser --system --group appuser
  USER appuser
  ```
- Docker image vulnerability scanning (Trivy) runs in every CI pipeline on every push.
- Images with `CRITICAL` or `HIGH` CVEs must not be pushed to Artifact Registry.

---

## 7. CI/CD Security Gates

Every CI run must include these security checks (zero tolerance for failures):
- `bandit -r src/ -ll` — Python SAST (minimum HIGH severity block).
- `pip-audit` — check all Python deps for known CVEs.
- `npm audit --audit-level=high` — check all Node.js deps.
- `trivy image` — container vulnerability scan.
- `trufflehog git` — detect secrets in commit history.
- `checkov -d infrastructure/terraform/` — Terraform misconfiguration scanning.

---

## 8. Audit Logging

All of the following must have audit logging enabled and logs retained for at least 1 year:
- **GCP Cloud Audit Logs**: `DATA_READ`, `DATA_WRITE`, `ADMIN_READ`, `ADMIN_WRITE`.
- **Databricks Audit Logs**: All workspace events (login, job runs, table access, permission changes).
- **Unity Catalog Audit Logs**: All `GRANT`, `REVOKE`, `READ`, `WRITE` operations on governed data.
- **GitHub Audit Log**: Organization-level events (PR merges, secret access, permission changes).

Audit logs must be exported to GCS and made queryable via Databricks SQL for compliance review.
