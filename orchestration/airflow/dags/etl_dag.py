from datetime import datetime

from airflow import DAG
from airflow.operators.python_operator import PythonOperator

from src.ingestion.connectors.s3_connector import S3Connector
from src.models.transformations import transform_data
from src.processing.batch.batch_jobs import BatchJob
from src.processing.streaming.stream_processor import StreamProcessor


def extract():
    s3 = S3Connector()
    data = s3.download_file("bucket_name", "data_file.csv")
    return data


def transform(data):
    transformed_data = transform_data(data)
    return transformed_data


def load(transformed_data):
    batch_job = BatchJob()
    batch_job.run_job(transformed_data)


def process_stream():
    stream_processor = StreamProcessor()
    stream_processor.start_processing()


default_args = {
    "owner": "data_team",
    "start_date": datetime(2023, 10, 1),
    "retries": 1,
}

dag = DAG("etl_dag", default_args=default_args, schedule_interval="@daily")

extract_task = PythonOperator(
    task_id="extract",
    python_callable=extract,
    dag=dag,
)

transform_task = PythonOperator(
    task_id="transform",
    python_callable=transform,
    op_kwargs={"data": '{{ task_instance.xcom_pull(task_ids="extract") }}'},
    dag=dag,
)

load_task = PythonOperator(
    task_id="load",
    python_callable=load,
    op_kwargs={
        "transformed_data": '{{ task_instance.xcom_pull(task_ids="transform") }}'
    },
    dag=dag,
)

process_stream_task = PythonOperator(
    task_id="process_stream",
    python_callable=process_stream,
    dag=dag,
)

extract_task >> transform_task >> load_task
load_task >> process_stream_task
