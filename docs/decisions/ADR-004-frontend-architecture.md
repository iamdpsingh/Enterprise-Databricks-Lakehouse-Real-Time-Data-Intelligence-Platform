# ADR 004: Frontend Observability & Business Intelligence Architecture

## 1. Status
**Accepted & Implemented in Production**

## 2. Executive Context
A modern data platform is essentially a "black box" to business stakeholders and even data engineers without a robust observability layer. 
- Traditional Business Intelligence (BI) tools (like Power BI, Tableau, or Looker) are excellent for static, historical reporting. However, they fail to provide the sub-second latency required to monitor real-time streaming pipelines. 
- We needed a "Command Center" capable of querying the Databricks SQL engine directly, calculating streaming throughputs dynamically, and presenting pipeline health (e.g., Data Quality Quarantines, Message Ingestion Rates) in an intuitive, animated interface that rivaled internal monitoring tools at FAANG companies.

### 2.1. The Compute Cost Challenge
Initially, the React UI executed heavy analytical aggregations (`SUM`, `AVG`, `COUNT DISTINCT`) directly against the Bronze (Raw) Delta tables dynamically on every page refresh.
- As the Bronze tables rapidly grew to millions of rows, dynamically computing these aggregates caused severe query latency on the dashboard (5-10 seconds per load).
- More critically, it placed an immense, expensive compute load on the Databricks Serverless SQL Warehouse. Polling a `COUNT DISTINCT` every 5 seconds on a billion-row table would bankrupt the cloud budget.

## 3. Decision
We built a bespoke, high-performance telemetry dashboard using **Next.js 14 (App Router)** and **React**, strictly integrating it with the highly-optimized **Gold Medallion Layer** to drastically reduce Databricks DBU consumption.

### 3.1. Implementation Details

#### 3.1.1. Gold Layer Pre-Materialization
Instead of the Next.js UI executing heavy math, the burden was shifted to the Databricks backend.
- The Databricks PySpark loop physically materializes the aggregations into static Gold Delta tables (`prod_catalog.ethereum.gold`) immediately after every micro-batch.
- The Next.js backend simply executes a `SELECT * FROM prod_catalog.ethereum.gold`. 
- **Result:** Dashboard load latency plummeted from 10 seconds to single-digit milliseconds. The Databricks SQL Warehouse only has to read a few kilobytes of pre-computed data, drastically reducing compute costs.

#### 3.1.2. Next.js Server Actions & Security
To ensure Databricks API tokens are never exposed to the client browser, all SQL queries are executed securely on the Node.js server.
- We utilize **Next.js Server Actions** (`"use server"` directives).
- We implemented the official `@databricks/sql` Node.js driver to manage secure, encrypted connections to the Databricks Serverless SQL Warehouse via the `DATABRICKS_SQL_HTTP_PATH`.

#### 3.1.3. Client-Side Throughput Calculation (Cost Optimization)
To calculate the real-time Message-per-Second (msg/sec) ingestion rate, we could have executed complex SQL time-window queries (e.g., `SELECT count(*) FROM table WHERE timestamp >= NOW() - 5 seconds`). However, this is computationally expensive to poll continuously.
- **The Solution:** We offloaded the math to the client's browser (React).
- The React frontend uses `useEffect` hooks to poll the Server Action every 5 seconds.
- The UI uses a React `useRef` hook to store the *previous* total row count in memory.
- The UI calculates: `(Current Total Rows - Previous Total Rows) / 5 seconds = Real-Time msg/sec`.
- **Result:** We achieve dynamic, real-time throughput monitoring without asking the Databricks SQL Warehouse to perform any temporal math, further reducing cloud costs.

#### 3.1.4. State-Driven Degradation
The UI is designed to gracefully represent the health of the pipeline without crashing.
- If the calculated ingestion rate drops to `0 msg/sec`, the pipeline status gracefully degrades to a gray `Idling` state in the UI.
- If the rate is `> 0 msg/sec`, it switches to a green `Streaming` state.
- If the Server Action throws an exception (e.g., the SQL Warehouse is suspended or network drops), the UI degrades to a red `Disconnected` state, alerting the engineer immediately.

## 4. Consequences & Trade-Offs
- **Positive - Blistering Performance:** By querying Gold tables instead of Bronze, and offloading math to the client browser, dashboard load latency is practically instant.
- **Positive - Cost Efficiency:** The Databricks SQL Warehouse is barely utilized, as it is only returning static, pre-computed rows.
- **Positive - Stakeholder Visibility:** The enterprise gains a highly custom, beautiful monitoring UI that provides absolute transparency into pipeline health and Data Quality Quarantines.
- **Negative - Full-Stack Overhead:** Maintaining a custom Next.js application introduces a new language (TypeScript) and a complex React framework to the Data Engineering team. This requires cross-functional skills (Full-Stack Data Engineering) rather than relying on standard BI drag-and-drop tools.
