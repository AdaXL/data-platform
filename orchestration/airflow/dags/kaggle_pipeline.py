from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Add src to path so we can import modules
sys.path.append(os.path.join(os.environ.get("AIRFLOW_HOME", "/app"), "src"))

from ingestion.kaggle_downloader import download_meta_kaggle_dataset
from processing.data_cleaner import clean_and_convert_to_parquet

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'kaggle_meta_pipeline',
    default_args=default_args,
    description='Pipeline to download and process Kaggle Meta dataset',
    start_date=datetime(2026, 1, 1), # Start date in the past
    schedule=timedelta(days=1),
    catchup=False, # Prevents backfills
) as dag:

    download_task = PythonOperator(
        task_id='download_kaggle_data',
        python_callable=download_meta_kaggle_dataset,
        op_kwargs={'download_path': '/app/data/test/raw'} # Adjust path for Airflow environment
    )

    process_task = PythonOperator(
        task_id='process_kaggle_data',
        python_callable=clean_and_convert_to_parquet,
        op_kwargs={'input_path': '/app/data/test/raw', 'output_path': '/app/data/test/processed'}
    )

    download_task >> process_task
