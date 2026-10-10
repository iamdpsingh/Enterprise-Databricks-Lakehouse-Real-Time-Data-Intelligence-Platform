# ADR 004: Frontend Observability & BI Architecture

## Status
Accepted

## Context
A modern data platform is a "black box" to business stakeholders and even data engineers without a robust observability layer. We need a "Command Center" that can query the Databricks SQL engine directly, calculate streaming throughputs dynamically, and present pipeline health (e.g., Data Quality Quarantines, Ingestion Rates) in an intuitive interface.

Initially, the UI executed heavy analytical aggregations (`SUM`, `AVG`, `COUNT DISTINCT`) directly against the Bronze (Raw) Delta tables dynamically. This caused high query latency on the dashboard and placed an expensive, unnecessary compute load on the Databricks SQL Warehouse.

## Decision
We will build a custom telemetry dashboard using **Next.js 14 (App Router)** and **React**, strictly integrating with the highly-optimized **Gold Medallion Layer**.

### Implementation Details:
1. **Gold Layer Integration:** The Next.js backend executes simple `SELECT * FROM prod_catalog.ethereum.gold` queries against pre-aggregated, materialized views instead of dynamically computing metrics on the fly.
2. **Server Actions:** All SQL queries are executed securely on the server using Next.js Server Actions. The `@databricks/sql` Node.js driver is used to connect to the Databricks Serverless SQL Warehouse.
3. **Real-Time Polling:** The React frontend utilizes `useEffect` hooks to poll the Server Actions every 5 seconds.
4. **Dynamic Delta Calculations:** The UI uses React `useRef` to store the previous polling state. By calculating `(Current Rows - Previous Rows) / 5 seconds`, the UI natively calculates the real-time Message-per-Second (msg/sec) ingestion rate client-side.
5. **State-Driven Degradation:** If the calculated rate is `0 msg/sec`, the pipeline status gracefully degrades to a gray `Idling` state. If `> 0`, it switches to `Streaming`. If the connection fails, it degrades to `Disconnected`.

## Consequences
- **Positive:** By querying the Gold tables instead of Bronze, dashboard load latency is reduced to single-digit milliseconds, and SQL compute costs are minimized.
- **Positive:** We achieve a highly custom, industrial-grade monitoring UI that rivals internal tools built at FAANG companies.
- **Negative:** Maintaining a custom React application introduces a new language (TypeScript) and framework to the data engineering team, requiring a broader skill set.
