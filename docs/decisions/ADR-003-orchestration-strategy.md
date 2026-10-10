# ADR 003: Pipeline Orchestration & Serverless Streaming Cost Optimization

## 1. Status
**Accepted & Implemented in Production**

## 2. Executive Context
An enterprise platform requires a robust orchestration engine to trigger streaming pipelines and manage the strict dependency graph between the Bronze, Silver, and Gold transformations. (e.g., The Gold layer must not calculate its aggregations until the Silver layer has successfully committed its current batch).

Our initial engineering design called for standard Spark Structured Streaming continuous triggers (e.g., `trigger(processingTime="10 seconds")`) running 24/7 on an Always-On dedicated compute cluster. 

**The Challenge:** 
1. **Cloud Compute Costs:** Maintaining a dedicated Spark cluster running 24/7 incurs massive idle cloud compute costs. We would be paying for Virtual Machine (VM) uptime even when the external APIs are silent and data velocity is zero.
2. **Databricks Serverless Restrictions:** To reduce costs, we attempted to migrate to Databricks Serverless Compute (which spins up instantly and charges only for active execution seconds). However, Databricks Serverless architecture strictly prohibits continuous infinite streaming triggers. Executing a continuous `processingTime` stream on a Serverless cluster causes the job to hang indefinitely or fail, as Serverless is fundamentally designed for ephemeral, bursty workloads.

We needed a mechanism to achieve the low-latency of continuous streaming while remaining 100% compliant with ephemeral Serverless execution patterns.

## 3. Decision
We will orchestrate the Medallion pipeline using **Serverless Micro-Batching wrapped in a native Python Continuous Loop**. We abandoned external orchestration tools (like Apache Airflow) for this specific real-time execution in favor of a tightly coupled Python control loop inside the Databricks Workspace.

### 3.1. Implementation Details

#### 3.1.1. The `AvailableNow` Spark Trigger
All PySpark Structured Streaming commands (`writeStream`) are configured strictly with `.trigger(availableNow=True)`. 
- Unlike a continuous trigger, `AvailableNow` instructs Spark to instantly wake up, evaluate all currently pending files in the Unity Catalog Volume, process them through the DAG, commit the ACID transaction to the Delta Log, and **safely terminate the stream query**.

#### 3.1.2. The Infinite Python Control Loop
Because `AvailableNow` terminates the stream, the pipeline would normally stop after one batch. To emulate 24/7 infinite streaming, we wrapped the PySpark execution commands inside a native Python `while True:` loop at the top level of the Databricks Master Notebook.
- **The Execution Flow:** 
  1. The loop starts.
  2. The Python agent triggers the Bronze `AvailableNow` stream.
  3. The Bronze stream terminates.
  4. The Python agent triggers the Silver `AvailableNow` stream.
  5. The Silver stream terminates.
  6. The Python agent runs `update_gold_layer()` (Batch SQL).
  7. `time.sleep(5)` is called to prevent hammering the Databricks control plane.
  8. The loop repeats indefinitely.

#### 3.1.3. Gold Layer Materialization
By orchestrating the pipeline sequentially in a Python loop, we implicitly solve the dependency graph problem. We guarantee that the `update_gold_layer()` batch SQL aggregations are only executed *after* the Bronze and Silver streams have completely finished processing their current micro-batch. This prevents the Gold layer from calculating incomplete metrics.

## 4. Consequences & Trade-Offs

- **Positive - Massive Cost Reduction:** Cloud compute costs (Databricks DBUs) are drastically reduced. Serverless compute spins up instantly to process the queue, and automatically scales down to zero when the Python loop is `sleep`ing or waiting for data. We only pay for the exact seconds the CPU is crunching data.
- **Positive - Serverless Compliance:** We achieve "near real-time" continuous ingestion latency (usually under 10 seconds) while remaining 100% compliant with Databricks Serverless infrastructure limitations.
- **Positive - DAG Enforcement:** The Medallion dependency graph is strictly and synchronously enforced (Bronze finishes -> Silver finishes -> Gold finishes), mathematically preventing dirty or incomplete reads in the Gold layer.
- **Negative - Custom Orchestration Debt:** Wrapping streaming queries in a Python `while True:` loop is an unconventional, custom orchestration pattern. It sidesteps standard Databricks Workflows (Jobs) or Apache Airflow, meaning built-in pipeline monitoring tools (like the Airflow UI) cannot track the individual micro-batches.
- **Negative - Session State:** If the Databricks notebook is manually cancelled or times out, the `while True:` loop dies and must be manually restarted by an engineer.
