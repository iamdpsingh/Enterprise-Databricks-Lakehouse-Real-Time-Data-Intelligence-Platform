# ADR 004: Comprehensive Frontend Observability & Next.js UI Architecture

## 1. Document Control
- **Status:** Accepted & Implemented in Production
- **Date:** October 2026
- **Author:** Principal Data Engineering / Full-Stack Engineering Team
- **Reviewers:** Head of Platform, Chief Data Officer (CDO)
- **Domain:** Data Observability & Telemetry

---

## 2. Table of Contents
1. Document Control
2. Table of Contents
3. Executive Summary
4. Core Business Context & Technical Drivers
5. The Architectural Dilemma: Observability Tools
   5.1. Alternative 1: Traditional BI (Tableau, PowerBI, Looker)
   5.2. Alternative 2: Open-Source Observability (Grafana + Prometheus)
   5.3. Alternative 3: Custom React Application (The Decision)
6. Deep Dive: Next.js Server Actions & Databricks SQL
   6.1. Securing the Databricks Token
   6.2. The @databricks/sql Node.js Driver
7. The Compute Cost Challenge: Bronze vs Gold
   7.1. The Bronze Polling Disaster
   7.2. The Gold Layer Materialization Pivot
8. Client-Side Telemetry: Offloading Math to the Browser
   7.1. Traditional Time-Window SQL Math
   7.2. React `useRef` and Delta Calculations
9. State-Driven Degradation UI
10. Infrastructure as Code & Deployment
11. Cost Projections & DBU Economics
12. Comprehensive FAQ
13. Glossary of Terms

---

## 3. Executive Summary
A modern data platform is essentially a "black box" to business stakeholders and even data engineers without a robust observability layer. This document formalizes the architectural decision to build a bespoke, real-time "Command Center" using **Next.js 14 (App Router)**. By integrating this custom React application directly with the highly-optimized **Gold Medallion Layer** via Databricks Serverless SQL, we achieve sub-second dashboard latency. Furthermore, by offloading the mathematical calculation of Message-per-Second (msg/sec) throughput to the client browser using React Hooks, we drastically reduce the compute load on the Databricks SQL Warehouse, generating significant cloud cost savings.

---

## 4. Core Business Context & Technical Drivers
Data Engineers need to know instantly if a pipeline is failing, if data is backing up in the Unity Catalog Volumes, or if the Dead Letter Queue (Quarantine) is spiking due to an upstream API change. 
- **Latency:** The dashboard must reflect reality within seconds. Waiting 15 minutes for a scheduled Tableau extract is unacceptable for a real-time platform.
- **Customization:** We need to render animated states (e.g., green `Streaming` badges vs red `Disconnected` badges) based on complex logic that standard BI drag-and-drop tools cannot support.
- **Security:** Databricks API tokens must never be exposed to the public internet or the client browser.

---

## 5. The Architectural Dilemma: Observability Tools

### 5.1. Alternative 1: Traditional BI (Tableau, PowerBI, Looker)
- **The Flaw:** These tools are excellent for static, historical reporting. However, they rely on scheduled extracts or DirectQuery modes that are notoriously slow. They cannot natively provide the sub-second, animated polling latency required to monitor a live streaming pipeline.
- **Verdict:** Rejected for real-time operational monitoring.

### 5.2. Alternative 2: Open-Source Observability (Grafana + Prometheus)
- **The Flaw:** Grafana is the industry standard for infrastructure monitoring. However, writing custom plugins to query Databricks Delta tables in real-time is highly complex. Furthermore, standing up a Grafana/Prometheus cluster introduces additional infrastructure to manage.
- **Verdict:** Rejected due to infrastructure overhead.

### 5.3. Alternative 3: Custom React Application (The Decision)
- **The Solution:** Next.js provides a unified frontend/backend framework. We can build a fully custom, heavily animated UI that polls a serverless backend.
- **Verdict:** Accepted. It provides ultimate flexibility and allows us to build a tool that rivals internal monitoring dashboards at FAANG companies.

---

## 6. Deep Dive: Next.js Server Actions & Databricks SQL

Connecting a web application directly to a Data Warehouse requires strict security boundaries.

### 6.1. Securing the Databricks Token
If the Databricks API token (PAT) was embedded in the React frontend, any user could open the Chrome Developer Tools, steal the token, and drop the entire enterprise database.
- We utilize **Next.js Server Actions** (the `"use server"` directive). 
- When the React component requests data, it calls a Server Action. This action executes entirely on the secure Node.js backend.
- The backend securely reads the `DATABRICKS_API_TOKEN` from the `.env` file (which is never sent to the browser) and executes the query.

### 6.2. The `@databricks/sql` Node.js Driver
We utilize the official Databricks SQL Node.js driver to manage connections to the Databricks Serverless SQL Warehouse.
- It handles Thrift protocol encryption automatically.
- It manages session states and cursor closing, preventing memory leaks on the Next.js server.

---

## 7. The Compute Cost Challenge: Bronze vs Gold

### 7.1. The Bronze Polling Disaster
Initially, the React UI executed heavy analytical aggregations (`SUM`, `AVG`, `COUNT DISTINCT`) directly against the Bronze (Raw) Delta tables dynamically on every page refresh.
- As the Bronze tables rapidly grew to millions of rows, dynamically computing these aggregates caused severe query latency (5-10 seconds per load).
- More critically, it placed an immense, expensive compute load on the Databricks Serverless SQL Warehouse. Polling a `COUNT DISTINCT` every 5 seconds on a billion-row table would bankrupt the cloud budget.

### 7.2. The Gold Layer Materialization Pivot
Instead of the Next.js UI executing heavy math, the burden was shifted to the Databricks PySpark backend.
- The Databricks pipeline physically materializes the aggregations into static Gold Delta tables (`prod_catalog.ethereum.gold`) immediately after every micro-batch via `update_gold_layer()`.
- The Next.js Server Action simply executes `SELECT * FROM prod_catalog.ethereum.gold`.
- **Result:** Dashboard load latency plummeted from 10 seconds to single-digit milliseconds. The Databricks SQL Warehouse only has to read a few kilobytes of pre-computed data, drastically reducing Databricks Unit (DBU) costs.

---

## 8. Client-Side Telemetry: Offloading Math to the Browser

Calculating the real-time Message-per-Second (msg/sec) ingestion throughput is a complex engineering problem.

### 8.1. Traditional Time-Window SQL Math
Typically, to calculate throughput, you would execute a temporal SQL query:
`SELECT count(*) / 5 AS msg_per_sec FROM bronze WHERE timestamp >= NOW() - INTERVAL 5 SECONDS`
- **The Flaw:** Executing this temporal math every 5 seconds against a massive Delta table is incredibly CPU-intensive for the Databricks SQL Warehouse.

### 8.2. React `useRef` and Delta Calculations (The Pivot)
We offloaded the mathematical calculation entirely to the client's browser (React).
1. The React frontend uses `useEffect` to poll the total row count every 5 seconds.
2. The UI uses a React `useRef` hook to store the *previous* total row count in the browser's memory without triggering a re-render.
3. When the new row count arrives, the UI calculates the delta: `(Current Total Rows - Previous Total Rows) / 5 seconds = Real-Time msg/sec`.
- **Result:** We achieve dynamic, real-time throughput monitoring without asking the Databricks SQL Warehouse to perform any temporal math, effectively making the UI compute "free".

---

## 9. State-Driven Degradation UI

An enterprise monitoring tool must gracefully represent the health of the pipeline without crashing or showing blank screens.
- **Idling (Gray):** If the calculated client-side ingestion rate drops to `0 msg/sec`, the pipeline status gracefully degrades to a gray state. This indicates the APIs are silent or the Serverless cluster is sleeping.
- **Streaming (Green):** If the rate is `> 0 msg/sec`, the UI automatically switches to a pulsing green state, indicating active data flow.
- **Disconnected (Red):** If the Server Action throws a Try/Catch exception (e.g., the SQL Warehouse is suspended, network drops, or the PAT token expires), the UI catches the error and degrades to a red state, alerting the engineer immediately.

---

## 10. Infrastructure as Code & Deployment

The Next.js application should be deployed via a Vercel CI/CD pipeline or containerized via Docker and deployed to Google Cloud Run.
- Environment variables (`NEXT_PUBLIC_DATABRICKS_SQL_HTTP_PATH`) must be injected at build time.
- The Databricks SQL Warehouse should be configured for "Serverless" with an aggressive Auto-Stop of 5 minutes to prevent idle billing when no users are viewing the dashboard.

---

## 11. Cost Projections & DBU Economics

- **Vercel / Cloud Run:** Hosting a Next.js application is virtually free (under $20/month).
- **Databricks SQL Serverless:** Because we only execute basic `SELECT *` queries against tiny Gold tables, queries execute in <50ms. The Serverless Warehouse spins up instantly, serves the query, and scales down. We project SQL Warehouse costs to be less than $50/month, compared to $2,000+/month if we were executing dynamic `COUNT DISTINCT` queries against the Bronze tables.

---

## 12. Comprehensive FAQ

**Q: Why use Next.js App Router instead of the older Pages Router?**
A: The App Router natively supports React Server Components and Server Actions. This allows us to securely execute Databricks Node.js driver code without writing explicit REST API routes (`/api/metrics`), reducing boilerplate code by 50%.

**Q: Can we embed this dashboard inside the Databricks UI?**
A: No. While Databricks SQL Dashboards are excellent, they do not support custom React animations, client-side Delta math, or sub-second polling loops without heavy visual tearing. A standalone web app is required for this level of customization.

**Q: Is `@databricks/sql` compatible with the Edge runtime?**
A: No. The driver relies on native Node.js TCP socket modules (for the Thrift protocol). The Server Actions must run on the Node.js runtime, not the Vercel Edge network.

---

## 13. Glossary of Terms

- **Next.js:** A React framework that enables server-side rendering and static site generation.
- **Server Action:** An asynchronous function that executes exclusively on the server, allowing secure database access without exposing credentials to the browser.
- **Thrift Protocol:** The underlying binary communication protocol used to connect to Databricks SQL Warehouses.
- **useRef:** A React hook that allows you to persist values between renders without triggering a new render (perfect for storing the "previous" row count).
- **useEffect:** A React hook that lets you synchronize a component with an external system (e.g., setting up the 5-second `setInterval` polling loop).
