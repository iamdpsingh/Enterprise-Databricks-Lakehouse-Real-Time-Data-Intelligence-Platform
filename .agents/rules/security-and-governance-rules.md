# Security & Governance Rules

## 1. Identity and Access Management (IAM)
- **Principle of Least Privilege:** Users and service accounts must only have access to the resources they need.
- **Service Accounts:** Use dedicated GCP Service Accounts and Databricks Service Principals for automated processes (CI/CD, automated jobs). Never use personal user credentials for automation.
- **SSO & MFA:** Enforce Single Sign-On and Multi-Factor Authentication for all human access to Databricks and GCP.

## 2. Secrets Management
- **No Hardcoded Secrets:** Never commit passwords, API keys, tokens, or private keys to the codebase.
- **GCP Secret Manager:** Use GCP Secret Manager as the central repository for sensitive configurations.
- **Databricks Secrets:** Map GCP Secret Manager secrets to Databricks Secret Scopes for use within pipelines.
- **GitHub Secrets:** Use GitHub Environment Secrets for CI/CD pipeline authentication.

## 3. Data Security and Privacy
- **Encryption at Rest:** Ensure all data in GCS and Delta Lake is encrypted at rest using Customer-Managed Encryption Keys (CMEK) where mandated by policy.
- **Encryption in Transit:** All communication between services must be encrypted using TLS.
- **PII Handling:** Identify and classify Personally Identifiable Information (PII). Implement dynamic data masking or tokenization in Unity Catalog for sensitive columns.
- **Row/Column Level Security:** Utilize Unity Catalog's row filters and column masks to restrict access to sensitive data based on user roles.

## 4. Unity Catalog Governance
- **Access Control:** Manage all data access grants via Unity Catalog SQL (`GRANT SELECT ON TABLE...`). Do not rely on underlying cloud storage IAM for data access control once registered in UC.
- **Auditing:** Enable and monitor Unity Catalog audit logs to track data access and modifications.
- **Data Lineage:** Leverage Unity Catalog's automated data lineage to track data flow and dependencies for compliance and impact analysis.

## 5. Infrastructure Security
- **Network Isolation:** Deploy Databricks workspaces in a customer-managed VPC (Secure Cluster Connectivity).
- **Vulnerability Scanning:** Ensure all Docker images are scanned for vulnerabilities in CI before being pushed to Artifact Registry.
- **Dependency Scanning:** Regularly scan Python and Node.js dependencies for known vulnerabilities.
