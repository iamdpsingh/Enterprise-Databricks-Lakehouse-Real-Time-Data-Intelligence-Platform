import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

DATASETS = ['ethereum', 'github', 'overture', 'reddit']

with DAG(
    'enterprise_lakehouse_pipeline',
    default_args=default_args,
    description='Triggers the Databricks Lakehouse Medallion Architecture Jobs for all 4 global datasets',
    schedule_interval='@hourly',
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['lakehouse', 'databricks', 'medallion', 'gcp'],
) as dag:

    start_pipeline = EmptyOperator(task_id='start_pipeline')
    end_pipeline = EmptyOperator(task_id='end_pipeline')
    
    # We will trigger parallel execution for all 4 pipelines
    for ds in DATASETS:
        # Note: In a real implementation, you'd fetch the specific job ID for each dataset's pipeline
        # from environment variables or a config lookup.
        job_id = int(os.environ.get(f"DATABRICKS_{ds.upper()}_JOB_ID", 1000))
        
        run_pipeline = DatabricksRunNowOperator(
            task_id=f'run_{ds}_pipeline',
            databricks_conn_id='databricks_default',
            job_id=job_id,
        )
        
        start_pipeline >> run_pipeline >> end_pipeline
