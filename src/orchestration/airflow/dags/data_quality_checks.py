import os
from datetime import datetime

from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    'owner': 'data-governance',
    'depends_on_past': False,
    'retries': 1,
}

with DAG(
    'lakehouse_data_quality_checks',
    default_args=default_args,
    description='Triggers standalone data quality and quarantine resolution jobs',
    schedule_interval='0 2 * * *', # Daily at 2 AM
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['quality', 'governance'],
) as dag:

    start_checks = EmptyOperator(task_id='start_checks')
    
    # Run data profiling on Silver layer
    profile_silver = DatabricksRunNowOperator(
        task_id='profile_silver_data',
        databricks_conn_id='databricks_default',
        job_id=int(os.environ.get("DATABRICKS_DQ_PROFILE_JOB_ID", 2001)),
    )
    
    # Check quarantine queue and alert if it exceeds threshold
    check_quarantine = DatabricksRunNowOperator(
        task_id='check_quarantine_queue',
        databricks_conn_id='databricks_default',
        job_id=int(os.environ.get("DATABRICKS_QUARANTINE_CHECK_JOB_ID", 2002)),
    )
    
    end_checks = EmptyOperator(task_id='end_checks')

    start_checks >> [profile_silver, check_quarantine] >> end_checks
