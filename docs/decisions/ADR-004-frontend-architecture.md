# ADR-004: Frontend Architecture & API Integration

## Status
Accepted

## Context
As the Enterprise Databricks Lakehouse platform grows, data consumers (e.g., product managers, analysts, executives) require real-time visibility into Lakehouse metrics, data quality, and pipeline health.

We need to establish a frontend architecture that is highly performant, visually premium, and decoupled from the heavy spark-based backend.

## Decision
We will adopt the following stack and design language for the Data Intelligence Platform UI:
1. **Frontend Framework:** Next.js (App Router, React 18+). It provides server-side rendering (SSR), static site generation (SSG), and seamless client-side interactivity.
2. **Backend/API Layer:** FastAPI. Next.js will **not** query Databricks SQL directly. Instead, it will fetch JSON from the FastAPI backend. FastAPI acts as the unified Data API layer, connecting to Databricks SQL Warehouses and handling caching, authentication, and connection pooling.
3. **Styling & Aesthetics:** Custom CSS modules/Vanilla CSS utilizing a **Premium Glassmorphism** design language.
   - Dark mode default (`#0a0a0f` backgrounds).
   - Translucent `rgba` surfaces with heavy backdrop blurring.
   - Subtle gradients and micro-animations for high-end polish.
   - Tailwind CSS is intentionally omitted to enforce a strict, bespoke CSS-variable-driven design system.

### Rationale
- **Decoupling:** By placing FastAPI between Next.js and Databricks, we abstract away database-specific drivers (`databricks-sql-connector`) from the frontend. This also allows other consumers (like Jupyter notebooks or mobile apps) to use the exact same API.
- **Performance:** Next.js provides excellent perceived performance and SEO (if applicable) through its App Router and streaming capabilities.
- **Aesthetics:** A premium, custom glassmorphism aesthetic builds immediate user trust and aligns with enterprise "Data Intelligence" branding better than standard component libraries like Material-UI or Bootstrap.
- **Maintainability:** Standardized CSS variables allow for easy theme adjustments without diving into thousands of utility classes.

## Consequences
- **Positive:** Beautiful, highly responsive user interface that data consumers will love.
- **Positive:** FastAPI provides a robust, typed API contract (OpenAPI/Swagger) that the frontend can rely on.
- **Negative:** Maintaining custom CSS for a complex dashboard can be time-consuming compared to using an off-the-shelf component library.
- **Mitigation:** We will build a strict internal design system (e.g., `MetricCard`, `DataTable`) to ensure CSS reusability and prevent ad-hoc styling.
