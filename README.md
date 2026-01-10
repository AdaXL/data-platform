# Data Platform Project

## Overview
This data platform project is designed to facilitate the ingestion, processing, storage, and analysis of data. It integrates various components to create a robust architecture for handling data workflows.

Recently updated to include analysis of the **Meta Kaggle** dataset, visualized using a Streamlit application.

## Project Structure
The project is organized into several key directories:

- **src**: Contains the source code for data ingestion, processing, storage, and models.
  - **ingestion**: Handles data ingestion from various sources.
    - **connectors**: Contains connectors for different data sources.
    - **kaggle_downloader.py**: Script to download the Meta Kaggle dataset.
  - **processing**: Manages data processing tasks, both batch and streaming.
  - **storage**: Defines the schema and documentation for data storage solutions.
  - **models**: Contains data transformation functions.
  - **common**: Includes utility functions used across the project.
  - **app.py**: Streamlit application for visualizing the data.

- **infra**: Contains infrastructure as code configurations.
  - **terraform**: Terraform scripts for provisioning infrastructure.
  - **k8s**: Kubernetes deployment configurations.

- **orchestration**: Manages orchestration of data workflows.
  - **airflow**: Contains Airflow DAGs for ETL processes.

- **dbt**: Contains dbt models and project configuration for data transformations.

- **analytics**: Includes reports and analysis tools.

- **docs**: Documentation for the architecture and usage of the platform.

- **tests**: Contains unit and integration tests for the project.

- **scripts**: Utility scripts for deployment and management.

- **configs**: Configuration files for environment settings.

- **.github**: GitHub workflows for CI/CD.

## Getting Started
To get started with the project, follow these steps:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd data-platform
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables by copying the example configuration:
   ```
   cp configs/.env.example .env
   ```
   
   **Note**: You will need to set up your Kaggle API credentials. Place your `kaggle.json` file in `~/.kaggle/` or set the `KAGGLE_USERNAME` and `KAGGLE_KEY` environment variables.

4. Download the Meta Kaggle dataset:
   ```
   python src/ingestion/kaggle_downloader.py
   ```

5. Run the Streamlit application:
   ```
   streamlit run src/app.py
   ```

6. (Optional) Run the rest of the platform using Docker:
   ```
   docker-compose up
   ```

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.
