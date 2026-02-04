import os

import duckdb
import pandas as pd
import streamlit as st

from agent.graph import SQLAgent
from agent.visualization import VisualizationAgent


# Initialize DuckDB connection
@st.cache_resource
def get_connection():
    con = duckdb.connect(database=":memory:")
    con.execute("INSTALL httpfs; LOAD httpfs;")
    # Configure S3/Remote access if env vars are present
    if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        con.execute(
            f"""
            SET s3_region='{os.getenv("AWS_REGION", "us-east-1")}';
            SET s3_access_key_id='{os.getenv("AWS_ACCESS_KEY_ID")}';
            SET s3_secret_access_key='{os.getenv("AWS_SECRET_ACCESS_KEY")}';
            SET s3_endpoint='{os.getenv("S3_ENDPOINT", "s3.amazonaws.com")}';
        """
        )
    return con


def load_file_into_duckdb(con, file_path, table_name=None):
    """
    Loads a single file (CSV, Parquet, JSON) into DuckDB.
    """
    if table_name is None:
        # Infer table name from filename
        base_name = os.path.basename(file_path)
        table_name = (
            os.path.splitext(base_name)[0].replace("-", "_").replace(" ", "_").lower()
        )

    try:
        # Determine file type and construct query
        if file_path.endswith(".parquet"):
            query = f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{file_path}')"
        elif file_path.endswith(".csv"):
            query = f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{file_path}')"
        elif file_path.endswith(".json"):
            query = f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_json_auto('{file_path}')"
        else:
            return None, "Unsupported file format"

        con.execute(query)
        return table_name, None
    except Exception as e:
        return None, str(e)


def main():
    st.set_page_config(page_title="DataMind: Universal Data Analyst", layout="wide")
    st.title("DataMind: Universal Data Analyst")

    # Sidebar for setup
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("DeepSeek API Key", type="password")
        if not api_key:
            st.warning("Please enter your DeepSeek API Key.")

        st.header("Data Sources")
        con = get_connection()

        # 1. File Upload
        uploaded_files = st.file_uploader(
            "Upload Data (CSV, Parquet, JSON)", accept_multiple_files=True
        )

        # 2. External Database Connection (Simplified)
        st.subheader("External Database")
        db_type = st.selectbox("Type", ["None", "Postgres", "MySQL", "S3"])

        if db_type == "S3":
            s3_path = st.text_input("S3 Path (s3://bucket/path/*.parquet)")
            if st.button("Connect S3"):
                if s3_path:
                    table_name = "s3_data"
                    try:
                        con.execute(
                            f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{s3_path}')"
                        )
                        st.success(f"Loaded S3 data into '{table_name}'")
                        if "loaded_tables" not in st.session_state:
                            st.session_state["loaded_tables"] = []
                        st.session_state["loaded_tables"].append(table_name)
                    except Exception as e:
                        st.error(f"Error connecting to S3: {e}")

        # Process Uploaded Files
        if uploaded_files:
            if "loaded_tables" not in st.session_state:
                st.session_state["loaded_tables"] = []

            for uploaded_file in uploaded_files:
                # Save to temp file to allow DuckDB to read it
                # In a real app, handle temp files more securely/robustly
                temp_path = f"temp_{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                table_name, error = load_file_into_duckdb(con, temp_path)
                if table_name:
                    if table_name not in st.session_state["loaded_tables"]:
                        st.session_state["loaded_tables"].append(table_name)
                    st.success(f"Loaded '{uploaded_file.name}' as table '{table_name}'")
                else:
                    st.error(f"Failed to load '{uploaded_file.name}': {error}")

                # Cleanup temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        if "loaded_tables" in st.session_state and st.session_state["loaded_tables"]:
            st.write("Active Tables:", list(set(st.session_state["loaded_tables"])))

            # Indexing for RAG
            if st.button("Index Schema for AI"):
                with st.spinner("Indexing schema..."):
                    # Extract schema info for RAG
                    tables_info = []
                    for table in st.session_state["loaded_tables"]:
                        try:
                            columns = con.execute(f"DESCRIBE {table}").fetchall()
                            col_str = ", ".join([f"{c[0]} ({c[1]})" for c in columns])
                            tables_info.append(
                                {"table_name": table, "columns": col_str}
                            )
                        except:
                            pass

                    # Initialize Agent just to access retriever (or make retriever standalone)
                    # Here we re-instantiate SQLAgent to get access to its retriever for indexing
                    # Ideally, we'd separate this logic.
                    temp_agent = SQLAgent(con, api_key if api_key else "dummy")
                    temp_agent.retriever.index_schema(tables_info)
                    st.success("Schema indexed! You can now ask questions.")

    # Main Chat Interface
    st.subheader("Ask a question about your data")
    user_query = st.text_input(
        "Query", "Show me the summary statistics for the users table."
    )

    if st.button("Analyze"):
        if not api_key:
            st.error("Please provide a DeepSeek API Key.")
            return

        if (
            "loaded_tables" not in st.session_state
            or not st.session_state["loaded_tables"]
        ):
            st.error("Please load data first.")
            return

        st.info("Agent is thinking...")

        # Initialize Agents
        sql_agent = SQLAgent(con, api_key)
        viz_agent = VisualizationAgent(api_key)

        # Run SQL Agent
        result_state = sql_agent.run(user_query)

        # Display Results
        st.markdown("### Generated SQL")
        st.code(result_state["sql_query"], language="sql")

        if result_state["error"]:
            st.error(f"Final Error: {result_state['error']}")
        elif isinstance(result_state["query_result"], pd.DataFrame):
            df = result_state["query_result"]
            st.markdown("### Results")
            st.dataframe(df)

            if not df.empty:
                st.info("Generating visualization...")

                # Run Visualization Agent
                # We use create_chart which handles fallback logic internally
                viz_config = viz_agent.suggest_visualization(df, user_query)

                if viz_config:
                    st.markdown("### Visualization")
                    st.caption(f"Reasoning: {viz_config.get('reasoning', 'N/A')}")

                    fig = viz_agent.create_chart(df, viz_config)
                    if fig:
                        st.plotly_chart(fig)
                    else:
                        st.warning("Could not create chart even after fallback.")
                else:
                    st.warning(
                        "Could not determine a suitable visualization for this data."
                    )


if __name__ == "__main__":
    main()
