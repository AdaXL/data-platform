import os
import sys

from dagster import job, op, repository

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from ingestion.kaggle_downloader import download_meta_kaggle_dataset
from processing.data_cleaner import clean_and_convert_to_parquet


@op
def download_op():
    download_meta_kaggle_dataset(download_path="data/raw")


@op
def process_op(start_after):
    clean_and_convert_to_parquet(input_path="data/raw", output_path="data/processed")


@job
def kaggle_pipeline_job():
    downloaded = download_op()
    process_op(downloaded)


@repository
def kaggle_repository():
    return [kaggle_pipeline_job]
