import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from airflow.operators.empty import EmptyOperator

# Standard default arguments for robust DAGs
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'enterprise_lakehouse_pipeline',
    default_args=default_args,
    description='Triggers the Databricks Lakehouse Medallion Architecture Jobs',
    schedule_interval='@hourly',
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['lakehouse', 'databricks', 'medallion'],
) as dag:

    start_pipeline = EmptyOperator(task_id='start_pipeline')
    
    # 1. Bronze Ingestion
    ingest_bronze = DatabricksRunNowOperator(
        task_id='ingest_raw_bronze',
        databricks_conn_id='databricks_default',
        job_id=int(os.environ.get("DATABRICKS_BRONZE_JOB_ID", 1001)),
    )
    
    # 2. Silver Transformations & CDC
    process_silver = DatabricksRunNowOperator(
        task_id='process_cleaned_silver',
        databricks_conn_id='databricks_default',
        job_id=int(os.environ.get("DATABRICKS_SILVER_JOB_ID", 1002)),
    )
    
    # 3. Gold Aggregations
    compute_gold = DatabricksRunNowOperator(
        task_id='compute_metrics_gold',
        databricks_conn_id='databricks_default',
        job_id=int(os.environ.get("DATABRICKS_GOLD_JOB_ID", 1003)),
    )
    
    end_pipeline = EmptyOperator(task_id='end_pipeline')

    # Define DAG dependencies (Linear Flow)
    start_pipeline >> ingest_bronze >> process_silver >> compute_gold >> end_pipeline
