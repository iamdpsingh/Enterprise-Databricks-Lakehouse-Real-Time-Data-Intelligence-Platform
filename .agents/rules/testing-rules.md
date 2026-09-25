# Testing Rules

## 1. Testing Philosophy
- **Shift Left:** Testing must happen as early as possible in the development lifecycle (locally and in CI).
- **Test-Driven Development (TDD):** Encouraged for complex transformations and business logic.
- **No Silent Failures:** Tests must strictly fail on errors. Warnings should be treated as errors in CI.

## 2. Unit Testing
- **Scope:** Test individual functions, classes, and methods in isolation.
- **Tools:** `pytest` for Python, `jest` for Next.js/TypeScript.
- **Mocking:** Mock external dependencies (Databricks APIs, GCP services, databases) to ensure unit tests run quickly and deterministically without requiring a live environment.
- **Coverage:** Minimum 80% code coverage required for new code.

## 3. Integration Testing
- **Scope:** Test interactions between components (e.g., API to Database, Pipeline to Storage).
- **Environment:** Run against a dedicated ephemeral test environment or isolated schema in the Dev environment.
- **Data:** Use small, synthetic datasets that cover edge cases, nulls, and expected data formats.

## 4. Data Quality Testing
- **Scope:** Ensure data flowing through the pipelines meets structural and business requirements.
- **Implementation:** Implement as assertions or expectations within the Databricks pipelines (e.g., using Delta Live Tables expectations or custom validation functions).
- **Checks:** Enforce schema, nullability, uniqueness, and custom business rules at the boundary between Bronze and Silver layers.
- **Quarantine:** Tests that fail row-level validation must route the offending data to a quarantine table.

## 5. End-to-End (E2E) / Pipeline Testing
- **Scope:** Validate the entire data flow from ingestion to Gold tables.
- **Execution:** Triggered post-deployment in the Staging environment.
- **Validation:** Assert that output data in Gold tables matches expected results based on known input datasets.

## 6. Infrastructure Testing
- **Scope:** Validate Terraform configurations.
- **Tools:** Use `tflint` for static analysis and `terraform plan` checks in CI.

## 7. Performance Testing
- **Scope:** Ensure pipelines and APIs meet SLA requirements under expected and peak loads.
- **Execution:** Run periodically in Staging or before major architectural changes.
