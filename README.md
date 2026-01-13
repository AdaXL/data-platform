# KaggleMind: An Autonomous Agentic SQL Analyst

## Overview
KaggleMind is an AI-powered system designed to analyze the Meta Kaggle dataset. It allows users to ask natural language questions, which are then converted into SQL queries, executed against a DuckDB backend, and visualized using Streamlit.

## Architecture
- **Data Tier**:
    - **Ingestion**: Airflow orchestrates daily downloads of Meta Kaggle data.
    - **Transformation**: PySpark cleans and converts CSVs to Parquet.
    - **Warehouse**: DuckDB for fast local analytical queries.
- **AI Tier**:
    - **Orchestration**: LangGraph (planned) for multi-agent workflows.
    - **LLM**: Integration with advanced LLMs for SQL generation and insight extraction.
- **Frontend**: Streamlit with Plotly for interactive visualizations.

## Project Structure
- **src**:
  - **ingestion**: `kaggle_downloader.py` for fetching data.
  - **processing**: `data_cleaner.py` for Spark-based transformation.
  - **app.py**: Streamlit application.
- **orchestration**: Airflow DAGs.

## Getting Started

### Prerequisites
- Python 3.8+
- Java (for PySpark)
- Kaggle API credentials

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd data-platform
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp configs/.env.example .env
   ```
   Ensure `KAGGLE_USERNAME` and `KAGGLE_KEY` are set.

4. **Run the Data Pipeline:**
   You can run the scripts manually or via Airflow.
   
   **Manual:**
   ```bash
   # Download data
   python src/ingestion/kaggle_downloader.py
   
   # Process data
   python src/processing/data_cleaner.py
   ```

5. **Run the Application:**
   ```bash
   streamlit run src/app.py
   ```

### Docker
Run the full stack:
```bash
docker-compose up --build
```

## Roadmap
- [x] Data Ingestion & Processing
- [x] Basic Streamlit UI
- [ ] LangGraph Multi-Agent System
- [ ] Semantic Layer & Vector DB
- [ ] FastAPI Backend

## License
MIT
