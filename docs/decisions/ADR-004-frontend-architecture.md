# ADR 004: Frontend Observability Architecture

## Status
Accepted

## Context
A modern data platform is a "black box" to business stakeholders and even data engineers without a robust observability layer. Traditional BI tools (like Power BI or Tableau) are excellent for historical reporting but fail to provide sub-second latency for monitoring real-time streaming pipelines. We need a "Command Center" that can query the Databricks SQL engine directly, calculate streaming throughputs dynamically, and present pipeline health (e.g., Data Quality Quarantines, Ingestion Rates) in an intuitive, animated interface.

## Decision
We will build a custom telemetry dashboard using **Next.js 14 (App Router)** and **React**.

### Implementation Details:
1. **Server Actions:** All SQL queries are executed securely on the server using Next.js Server Actions. The `@databricks/sql` Node.js driver is used to connect to the Databricks Serverless SQL Warehouse.
2. **Real-Time Polling:** The React frontend utilizes `useEffect` hooks to poll the Server Actions every 5 seconds.
3. **Dynamic Delta Calculations:** The UI uses React `useRef` to store the previous polling state. By calculating `(Current Rows - Previous Rows) / 5 seconds`, the UI natively calculates the real-time Message-per-Second (msg/sec) ingestion rate without burdening Databricks with complex time-series queries.
4. **State-Driven CSS:** If the calculated ingestion rate is `0 msg/sec`, the pipeline status gracefully degrades to a gray `Idling` state. If it is `> 0`, it switches to a green `Streaming` state. If the SQL connection fails, it degrades to a red `Disconnected` state.

## Consequences
- **Positive:** We achieve a highly custom, industrial-grade monitoring UI that rivals internal tools built at FAANG companies.
- **Positive:** Business logic for rate calculation is offloaded to the client browser, saving Databricks SQL compute costs.
- **Negative:** Maintaining a custom React application introduces a new language (TypeScript) and framework to the data engineering team, requiring a broader skill set.
