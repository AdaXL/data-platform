# Makefile for Data Platform Project

.PHONY: all clean install run test

all: install

install:
    pip install -r requirements.txt

run:
    python -m src.ingestion.stream_consumer

test:
    pytest tests/unit

clean:
    find . -type d -name "__pycache__" -exec rm -r {} +