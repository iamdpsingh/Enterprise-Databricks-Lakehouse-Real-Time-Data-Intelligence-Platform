# ADR 003: Pipeline Orchestration & Serverless Streaming Strategy

## Status
Accepted

## Context
An enterprise platform requires a robust orchestration engine to trigger streaming pipelines and manage the dependency graph between the Bronze, Silver, and Gold transformations. 

Our initial design called for standard Spark Structured Streaming triggers (`trigger(processingTime="10 seconds")`) running 24/7. However, **Databricks Serverless Compute architecture strictly prohibits continuous infinite streaming triggers**. Executing a continuous stream on Serverless causes the job to hang indefinitely or fail.

If we provisioned a dedicated "Always-On" cluster to support continuous streaming, we would incur massive idle cloud compute costs, paying for VM up-time even when data velocity is low.

## Decision
We will orchestrate the Bronze, Silver, and Gold pipelines using **Serverless Micro-Batching wrapped in a native Python Continuous Loop**.

### Implementation Details:
1. **AvailableNow Trigger:** All PySpark `writeStream` commands are configured with `.trigger(availableNow=True)`. This forces Spark to process all currently available files in the Unity Catalog Volume, commit the ACID transaction, and safely terminate the stream query.
2. **Infinite Python Wrapper:** We wrap the sequential execution of the Bronze, Silver, and Gold streams inside a native Python `while True:` loop inside the Databricks Master Notebook.
3. **Gold Layer Execution:** After the streaming queries gracefully terminate, the loop executes `update_gold_layer()` to run standard Spark SQL batch queries, materializing the Rollup aggregations before sleeping for 5 seconds and repeating.

## Consequences
- **Positive:** We achieve "near real-time" continuous ingestion while remaining 100% compliant with Databricks Serverless limitations.
- **Positive:** Cloud compute costs are drastically reduced. Serverless compute spins up instantly to process the queue, and automatically scales down to zero when the Python loop is `sleep`ing or waiting for data.
- **Positive:** The Medallion dependency graph is strictly enforced (Bronze finishes -> Silver finishes -> Gold finishes), preventing dirty reads.
- **Negative:** Wrapping streaming queries in a Python `while True:` loop is an unconventional, custom orchestration pattern that sidesteps standard Databricks Workflows (Jobs), requiring engineers to manually run the notebook cell.
