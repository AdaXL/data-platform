import streamlit as st
import duckdb
import os
import plotly.express as px
import pandas as pd
from agent.graph import SQLAgent

# Initialize DuckDB connection
@st.cache_resource
def get_connection():
    con = duckdb.connect(database=':memory:')
    con.execute("INSTALL httpfs; LOAD httpfs;")
    if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        con.execute(f"""
            SET s3_region='{os.getenv("AWS_REGION", "us-east-1")}';
            SET s3_access_key_id='{os.getenv("AWS_ACCESS_KEY_ID")}';
            SET s3_secret_access_key='{os.getenv("AWS_SECRET_ACCESS_KEY")}';
            SET s3_endpoint='{os.getenv("S3_ENDPOINT", "s3.amazonaws.com")}';
        """)
    return con

def load_data_into_duckdb(con, data_path='data/processed'):
    is_remote = data_path.startswith('s3://') or data_path.startswith('http')
    if not is_remote and not os.path.exists(data_path):
        return False
    
    tables = {
        'users': 'users',
        'competitions': 'competitions',
        'user_achievements': 'user_achievements',
        'forum_messages': 'forum_messages',
        'user_followers': 'user_followers'
    }
    
    loaded_tables = []
    for table_name, file_name in tables.items():
        if is_remote:
            file_path = f"{data_path.rstrip('/')}/{file_name}"
            path_check = True
        else:
            file_path = os.path.join(data_path, file_name)
            path_check = os.path.exists(file_path)

        if path_check:
            try:
                query = f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{file_path}/*.parquet')"
                con.execute(query)
                loaded_tables.append(table_name)
            except Exception as e:
                if not is_remote:
                    st.error(f"Error loading {table_name}: {e}")
    return loaded_tables

def main():
    st.set_page_config(page_title="KaggleMind", layout="wide")
    st.title("KaggleMind: Agentic SQL Analyst")
    
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("DeepSeek API Key", type="password")
        if not api_key:
            st.warning("Please enter your DeepSeek API Key.")
            
        st.header("System Status")
        con = get_connection()
        
        if st.button("Reload Data"):
            data_source = os.getenv("DATA_PATH", "data/processed")
            with st.spinner("Loading data into DuckDB..."):
                loaded_tables = load_data_into_duckdb(con, data_path=data_source)
                if loaded_tables:
                    st.success(f"Loaded tables: {', '.join(loaded_tables)}")
                    st.session_state['loaded_tables'] = loaded_tables
                else:
                    st.error("Processed data not found.")
        
        if 'loaded_tables' in st.session_state:
            st.write("Active Tables:", st.session_state['loaded_tables'])

    st.subheader("Ask a question about the Kaggle dataset")
    user_query = st.text_input("Query", "Which Kaggle Grandmasters have the highest conversion rate from forum posts to competition gold medals?")
    
    if st.button("Analyze"):
        if not api_key:
            st.error("Please provide a DeepSeek API Key.")
            return

        if 'loaded_tables' not in st.session_state or not st.session_state['loaded_tables']:
            st.error("Please load data first.")
            return

        st.info("Agent is thinking (LangGraph)...")
        
        # Initialize Agent
        agent = SQLAgent(con, api_key)
        
        # Run Agent
        result_state = agent.run(user_query)
        
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
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0 and len(df.columns) > 1:
                    non_numeric_cols = df.select_dtypes(exclude=['number']).columns
                    x_col = non_numeric_cols[0] if len(non_numeric_cols) > 0 else df.columns[0]
                    y_col = numeric_cols[0]
                    
                    st.markdown("### Visualization")
                    fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
                    st.plotly_chart(fig)

if __name__ == "__main__":
    main()
