# Makefile for Data Platform Project

.PHONY: all clean install run test download process app dagster docker-up docker-down

all: install

install:
	pip install -r requirements.txt

# Data Pipeline Steps
download:
	python src/ingestion/kaggle_downloader.py

process:
	python src/processing/data_cleaner.py

# Run the Streamlit App
app:
	streamlit run src/app.py

# Run Dagster UI
dagster:
	dagster dev -f orchestration/dagster/repository.py -p 3000

# Testing
test:
	python -m unittest discover tests/unit

# Docker commands
docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	rm -rf data/processed/*
