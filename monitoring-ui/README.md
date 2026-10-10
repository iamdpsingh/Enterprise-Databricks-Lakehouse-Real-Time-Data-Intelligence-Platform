# Next.js Command Center (Monitoring UI)

This directory contains the custom-built **Enterprise Command Center**—a Next.js 14 application designed to provide real-time observability into the Databricks Lakehouse.

## 🌟 Features
- **Real-Time Telemetry:** Polls Databricks SQL every 5 seconds to calculate live Message-per-Second (msg/sec) ingestion rates natively on the client.
- **Dynamic Status Flags:** Automatically detects if pipelines are `Streaming (GCP)`, `Idling`, or `Disconnected` based purely on live data movement.
- **Data Quality Alerts:** Directly queries the `quality.quarantine` table to surface failing records and schema violations instantly.
- **Serverless Architecture:** Utilizes Next.js Server Actions to execute Databricks SQL queries securely on the backend, preventing token leakage to the browser.
- **Premium Aesthetics:** Built with custom CSS glassmorphism, Framer Motion staggered animations, and modern typography to provide an executive-level presentation.

## 🛠️ Tech Stack
- Next.js 14 (App Router)
- React 18
- TypeScript
- `@databricks/sql`
- Framer Motion

## 🚀 Getting Started

Ensure you have populated the `.env` file at the root of the project with your Databricks API Token and SQL HTTP Path.

```bash
# 1. Install dependencies
npm install

# 2. Start the development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result. The dashboard will automatically attempt to connect to your Databricks cluster and begin charting the Bronze table throughput.
