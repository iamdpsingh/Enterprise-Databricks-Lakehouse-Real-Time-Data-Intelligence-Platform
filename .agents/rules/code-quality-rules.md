# Code Quality & Standards Rules

## 1. Python Standards
- **Formatting:** Use `ruff format` to enforce a consistent code style.
- **Linting:** Use `ruff check` to catch programmatic errors and enforce style guidelines.
- **Type Hinting:** Use static typing (`mypy`) for all function signatures and complex variables.
- **Modularity:** Keep functions small (under 50 lines ideally) and focused on a single responsibility.
- **Docstrings:** Use Google-style docstrings for all classes, methods, and functions.

## 2. PySpark Standards
- **UDFs:** Avoid User Defined Functions (UDFs) if a native Spark SQL function exists. If necessary, use Pandas UDFs (Vectorized UDFs) for performance.
- **Joins:** Explicitly specify join conditions and types. Be mindful of broadcast joins for smaller datasets to avoid shuffles.
- **Immutability:** Treat DataFrames as immutable. Chain transformations cleanly.

## 3. SQL Standards
- **Formatting & Linting:** Use `sqlfluff` to enforce consistent SQL formatting.
- **Capitalization:** Uppercase SQL keywords (SELECT, FROM, WHERE), lowercase table and column names.
- **Readability:** Use Common Table Expressions (CTEs) instead of deeply nested subqueries.
- **Explicit Columns:** Never use `SELECT *` in production views or pipelines. List columns explicitly.

## 4. Next.js & TypeScript Standards
- **Strict Typing:** Enable strict mode in `tsconfig.json`. Avoid using `any`.
- **Linting & Formatting:** Use `eslint` and `prettier`.
- **Component Design:** Keep React components small, focused, and reusable. Separate business logic from presentation.

## 5. General Code Review Guidelines
- **Self-Review:** Review your own code before requesting a review from others.
- **Constructive Feedback:** Reviews should focus on logic, security, and architecture. Style issues should be caught by automated linters in CI.
- **No Rubber Stamping:** Every PR must be genuinely reviewed by at least one other engineer.
