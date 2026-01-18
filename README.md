# KaggleMind: An Autonomous Agentic SQL Analyst

## Overview
KaggleMind is an advanced AI-powered system designed to analyze the Meta Kaggle dataset. It leverages a **multi-agent architecture** to autonomously plan, generate, execute, and correct SQL queries, allowing users to ask complex natural language questions and receive accurate data visualizations.

## Architecture

### Data Tier
- **Ingestion**:
  - `src/ingestion/kaggle_downloader.py`: Downloads specific Meta Kaggle tables (`Users`, `Competitions`, `UserAchievements`, etc.) via the Kaggle API.
  - **Orchestration**: Airflow DAG (`orchestration/airflow/dags/kaggle_pipeline.py`) manages the daily sync pipeline.
- **Transformation**:
  - `src/processing/data_cleaner.py`: Uses **PySpark** to clean raw CSVs and convert them into optimized **Parquet** files.
- **Warehouse**:
  - **DuckDB**: Acts as a serverless OLAP engine to query Parquet files directly (supports local disk or remote S3/Supabase storage).

### AI Tier (Agentic System)
- **Orchestration**: **LangGraph** (`src/agent/graph.py`) manages the stateful workflow of the agent.
- **RAG (Retrieval-Augmented Generation)**:
  - `src/agent/rag_retriever.py`: Uses **ChromaDB** to store semantic descriptions of the schema. It retrieves only the relevant table schemas for a given user query, reducing context window usage and improving accuracy.
- **Self-Correction Loop**: The agent executes the generated SQL against DuckDB. If an error occurs (e.g., syntax error, missing column), the error is fed back into the LLM to autonomously fix the query.
- **LLM**: Powered by **DeepSeek-V3** (via OpenAI-compatible API) for high-performance code generation.

### Frontend
- **Streamlit**: Provides an interactive chat interface (`src/app.py`).
- **Plotly**: Automatically visualizes query results based on data types.

## Project Structure
```
data-platform/
├── src/
│   ├── agent/              # AI Agent Logic
│   │   ├── graph.py        # LangGraph workflow definition
│   │   └── rag_retriever.py # ChromaDB schema retrieval
│   ├── ingestion/          # Data Ingestion
│   │   └── kaggle_downloader.py
│   ├── processing/         # Data Transformation
│   │   └── data_cleaner.py # PySpark ETL
│   └── app.py              # Streamlit Frontend
├── orchestration/
│   └── airflow/dags/       # Airflow DAGs
│       └── kaggle_pipeline.py
├── data/                   # Local data storage (raw/processed)
├── requirements.txt
├── docker-compose.yml
├── Makefile
└── .pre-commit-config.yaml
```

## Getting Started

### Prerequisites
- Python 3.9+
- Java 17 (for PySpark)
- Kaggle API credentials
- DeepSeek API Key

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

3. **Install Pre-commit Hooks:**
   ```bash
   pre-commit install
   ```

4. **Set up environment variables:**
   ```bash
   cp configs/.env.example .env
   ```
   Ensure `KAGGLE_USERNAME`, `KAGGLE_KEY`, and `DEEPSEEK_API_KEY` are set.

5. **Run the Data Pipeline:**
   You can use the Makefile shortcuts:

   ```bash
   # Download specific tables
   make download

   # Process CSV to Parquet
   make process
   ```

6. **Run the Application:**
   ```bash
   make app
   ```
   Enter your DeepSeek API Key in the sidebar to start analyzing.

### Docker
Run the full stack including Airflow and Streamlit:
```bash
make docker-up
```

## Development
- **Linting & Formatting**: This project uses `black`, `isort`, and `flake8`.
  ```bash
  pre-commit run --all-files
  ```
- **Testing**:
  ```bash
  make test
  ```

## Roadmap
- [x] Data Ingestion & Processing
- [x] Basic Streamlit UI
- [ ] LangGraph Multi-Agent System
- [ ] Semantic Layer & Vector DB
- [ ] FastAPI Backend

## Features
- **Natural Language to SQL**: Ask questions like "Which Grandmasters have the highest conversion rate from forum posts to gold medals?"
- **Schema-Aware RAG**: The agent understands the specific schema of the Meta Kaggle dataset.
- **Auto-Correction**: If the agent writes bad SQL, it fixes it automatically.
- **Visualizations**: Dynamic charts generated from query results.

## License
MIT
