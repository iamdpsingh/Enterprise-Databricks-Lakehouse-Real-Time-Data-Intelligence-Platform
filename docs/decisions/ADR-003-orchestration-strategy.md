# ADR 003: Comprehensive Pipeline Orchestration & Serverless Streaming Cost Optimization

## 1. Document Control
- **Status:** Accepted & Implemented in Production
- **Date:** October 2026
- **Author:** Principal Data Engineering Team
- **Reviewers:** FinOps Board, Lead Cloud Architect
- **Domain:** Pipeline Orchestration & Cloud Economics

---

## 2. Table of Contents
1. Document Control
2. Table of Contents
3. Executive Summary
4. Core Business Context & Technical Drivers
5. The Architectural Dilemma: Orchestration Paradigms
   5.1. Alternative 1: Apache Airflow (External Orchestration)
   5.2. Alternative 2: Databricks Workflows (Internal Orchestration)
   5.3. Alternative 3: Native Python Control Loop (The Pivot)
6. Deep Dive: The Serverless Streaming Bottleneck
   6.1. The Cost of "Always-On" Streaming
   6.2. Databricks Serverless Restrictions
7. Implementation: The AvailableNow Micro-Batch Engine
   7.1. PySpark Trigger Configuration
   7.2. Emulating 24/7 Processing
   7.3. DAG Dependency Enforcement
8. The Gold Layer Materialization Strategy
9. FinOps: Cost Projections & DBU Economics
10. Operational Considerations
11. Disaster Recovery & Business Continuity
12. Comprehensive FAQ
13. Glossary of Terms

---

## 3. Executive Summary
An enterprise real-time data platform requires a highly robust orchestration engine to trigger streaming pipelines and manage the strict dependency graph between the Bronze, Silver, and Gold transformations. The Gold layer must absolutely never calculate its aggregations until the Silver layer has successfully committed its current batch, otherwise dirty reads occur.

Our initial engineering design called for standard Spark Structured Streaming continuous triggers (e.g., `trigger(processingTime="10 seconds")`) running 24/7 on an Always-On dedicated compute cluster. This document details why that architecture was scrapped due to catastrophic cloud compute costs and Databricks Serverless restrictions, and formally records our pivot to a **Serverless Micro-Batching engine wrapped in a native Python Continuous Loop**.

---

## 4. Core Business Context & Technical Drivers
The primary driver for this architectural pivot was **FinOps (Cloud Economics)**.
- Maintaining a dedicated Spark cluster running 24/7 incurs massive idle cloud compute costs. We would be paying for Virtual Machine (VM) uptime even when the external APIs are silent and data velocity is zero.
- To reduce costs, we attempted to migrate to Databricks Serverless Compute (which spins up instantly and charges only for active execution seconds). 
- However, Databricks Serverless architecture strictly prohibits continuous infinite streaming triggers. Executing a continuous `processingTime` stream on a Serverless cluster causes the job to hang indefinitely or fail, as Serverless is fundamentally designed for ephemeral, bursty workloads.

We needed a mechanism to achieve the low-latency of continuous streaming while remaining 100% compliant with ephemeral Serverless execution patterns.

---

## 5. The Architectural Dilemma: Orchestration Paradigms

Before arriving at our custom Python loop, we evaluated industry-standard orchestration tools.

### 5.1. Alternative 1: Apache Airflow (External Orchestration)
Airflow is the industry standard for Data Engineering DAGs.
- **The Flaw:** Managing a highly-available Airflow cluster (e.g., Cloud Composer on GCP) introduces immense infrastructure overhead, security complexities, and fixed costs. Furthermore, triggering Databricks Serverless jobs via the Airflow REST API introduces network latency and polling complexities (Airflow has to constantly ping Databricks to check if the micro-batch is done).
- **Verdict:** Rejected due to operational bloat and unnecessary fixed costs.

### 5.2. Alternative 2: Databricks Workflows (Internal Orchestration)
Databricks Workflows (Jobs) are natively integrated into the workspace.
- **The Flaw:** Workflows are excellent for standard hourly or daily batch jobs. However, trying to schedule a Workflow to run every 10 seconds to emulate a continuous stream often results in the Databricks control plane rate-limiting the workspace or causing scheduling collisions (Run 2 starts before Run 1 finishes).
- **Verdict:** Rejected due to micro-batching constraints.

### 5.3. Alternative 3: Native Python Control Loop (The Pivot)
We abandoned external orchestration tools for this specific real-time execution in favor of a tightly coupled Python control loop executing directly inside a Databricks Interactive Notebook.
- **Verdict:** Accepted. It allows synchronous execution of the Bronze, Silver, and Gold layers sequentially within milliseconds, without control-plane latency.

---

## 6. Deep Dive: The Serverless Streaming Bottleneck

### 6.1. The Cost of "Always-On" Streaming
In standard Spark, you initialize a stream using `df.writeStream.trigger(processingTime="10 seconds").start()`. The Spark Driver and Workers stay alive indefinitely. If you have a 4-node cluster, you are paying for 4 VMs 24 hours a day, 7 days a week, 365 days a year. This can easily cost $50,000+ per year in compute alone for a single pipeline.

### 6.2. Databricks Serverless Restrictions
Databricks Serverless aims to solve this by providing instant compute. You submit a query, Databricks instantly allocates CPUs from a warm pool, executes the query, and reclaims the CPUs. Because the CPUs are meant to be reclaimed, Databricks literally blocks you from running an infinite `processingTime` stream. If you attempt it, the Databricks control plane will aggressively terminate your job.

---

## 7. Implementation: The AvailableNow Micro-Batch Engine

To solve the Serverless restriction while keeping costs at zero during idle periods, we engineered a custom micro-batch orchestrator.

### 7.1. PySpark Trigger Configuration
All PySpark Structured Streaming commands (`writeStream`) are configured strictly with `.trigger(availableNow=True)`. 
- Unlike a continuous trigger, `AvailableNow` instructs Spark to instantly wake up, evaluate all currently pending files in the Unity Catalog Volume, process them through the DAG, commit the ACID transaction to the Delta Log, and **safely terminate the stream query**.
- Once the stream terminates, the Serverless cluster reclaims the CPUs.

### 7.2. Emulating 24/7 Processing
Because `AvailableNow` terminates the stream, the pipeline would normally stop after one batch. To emulate 24/7 infinite streaming, we wrapped the PySpark execution commands inside a native Python `while True:` loop.

```python
import time

while True:
    print("Initiating Micro-Batch...")
    
    # 1. Start Bronze Stream (AvailableNow)
    bronze_query = spark.readStream...writeStream.trigger(availableNow=True).start()
    bronze_query.awaitTermination() # The loop pauses here until Bronze is 100% finished
    
    # 2. Start Silver Stream (AvailableNow)
    silver_query = spark.readStream...writeStream.trigger(availableNow=True).start()
    silver_query.awaitTermination() # The loop pauses here until Silver is 100% finished
    
    # 3. Execute Gold Rollups
    update_gold_layer()
    
    # 4. Rest
    print("Micro-Batch Complete. Sleeping for 5 seconds to prevent control-plane throttling.")
    time.sleep(5)
```

### 7.3. DAG Dependency Enforcement
Notice `bronze_query.awaitTermination()`. This is the crux of the architecture. By running the streams synchronously within the Python loop, we implicitly solve the DAG dependency problem. We guarantee that the Silver stream will never start until the Bronze stream has fully committed its data to the Delta log.

---

## 8. The Gold Layer Materialization Strategy
By enforcing the synchronous DAG, we guarantee that the `update_gold_layer()` batch SQL aggregations are only executed *after* the Bronze and Silver streams have completely finished processing their current micro-batch. This mathematically prevents the Gold layer from calculating incomplete metrics or experiencing dirty reads. The Next.js dashboard will always query a perfectly cohesive, fully committed Gold state.

---

## 9. FinOps: Cost Projections & DBU Economics

This architecture achieves massive cost reductions.
- **Compute:** Serverless compute spins up instantly to process the queue, and automatically scales down to zero when the Python loop is `sleep`ing or waiting for data. We only pay for the exact seconds the CPU is crunching data.
- **Storage:** Because we use Databricks Unity Catalog Volumes (backed by GCS), we pay standard Google Cloud Storage rates (~$0.02 per GB).
- **Projection:** Compared to an Always-On dedicated cluster ($50,000/year), this Serverless Micro-batching architecture is projected to cost less than $5,000/year for equivalent throughput, representing a 90% reduction in Cloud OPEX.

---

## 10. Operational Considerations

- **Session State:** Because the orchestration relies on a Python `while True:` loop running in an interactive Databricks Notebook, if the notebook is manually cancelled, or if the Databricks Workspace experiences a total outage causing the notebook session to die, the pipeline stops. It must be manually restarted by an engineer.
- **Monitoring:** We cannot use Airflow UIs to monitor this. Instead, we rely entirely on the custom Next.js Command Center to alert us if the throughput drops to 0 msg/sec, indicating the loop has died.

---

## 11. Disaster Recovery & Business Continuity

If the Databricks notebook dies, data will begin queuing up in the Unity Catalog Volumes.
- **RTO (Recovery Time Objective):** < 5 minutes. An engineer simply opens the notebook and hits "Run".
- **RPO (Recovery Point Objective):** Zero. Because Auto Loader uses RocksDB to track file hashes, when the notebook is restarted, it will instantly find all the queued files in the Volume, process them in a massive catch-up micro-batch, and restore the pipeline to real-time without duplicating a single record.

---

## 12. Comprehensive FAQ

**Q: Why use `AvailableNow=True` instead of `Once=True`?**
A: `Once=True` is deprecated in modern Spark. Furthermore, `Once` forces Spark to process the entire backlog of files in a single massive batch, which can cause Out-Of-Memory (OOM) errors. `AvailableNow` is intelligent; it breaks the backlog into smaller, manageable micro-batches automatically, ensuring the cluster never crashes.

**Q: Does the `time.sleep(5)` cause data latency?**
A: Yes, it introduces a hard 5-second floor to our latency. However, sub-second latency is not required for our business use cases (executive dashboards). 5-10 second latency is considered "near real-time" and is perfectly acceptable, especially given the 90% cost savings.

---

## 13. Glossary of Terms

- **DAG (Directed Acyclic Graph):** A conceptual representation of the sequence of tasks in a data pipeline, ensuring tasks execute in the correct dependent order.
- **DBU (Databricks Unit):** The metric used by Databricks to bill for compute usage.
- **FinOps:** Cloud Financial Management; the practice of bringing financial accountability to the variable spend model of cloud computing.
- **Micro-Batching:** Processing streaming data in small, discrete chunks rather than record-by-record.
- **RPO (Recovery Point Objective):** The maximum acceptable amount of data loss measured in time.
- **RTO (Recovery Time Objective):** The maximum acceptable amount of time the system can be offline before business impact occurs.
