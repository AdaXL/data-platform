import streamlit as st
import duckdb
import os
import plotly.express as px
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Initialize DuckDB connection
@st.cache_resource
def get_connection():
    con = duckdb.connect(database=':memory:')
    # Install and load httpfs for S3/Remote support
    con.execute("INSTALL httpfs; LOAD httpfs;")
    
    # Check for S3 credentials in env vars
    if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        # Note: These settings work for both AWS S3 and Supabase Storage (S3 compatible)
        con.execute(f"""
            SET s3_region='{os.getenv("AWS_REGION", "us-east-1")}';
            SET s3_access_key_id='{os.getenv("AWS_ACCESS_KEY_ID")}';
            SET s3_secret_access_key='{os.getenv("AWS_SECRET_ACCESS_KEY")}';
            SET s3_endpoint='{os.getenv("S3_ENDPOINT", "s3.amazonaws.com")}';
        """)
    return con

def load_data_into_duckdb(con, data_path='data/processed'):
    """
    Loads Parquet files from the processed directory into DuckDB tables.
    """
    is_remote = data_path.startswith('s3://') or data_path.startswith('http')
    
    if not is_remote and not os.path.exists(data_path):
        return False
    
    tables = {
        # 'users': 'users',
        'competitions': 'competitions',
        # 'user_achievements': 'user_achievements',
        # 'forum_messages': 'forum_messages',
        'user_followers': 'user_followers'
    }
    
    loaded_tables = []
    for table_name, file_name in tables.items():
        if is_remote:
            # Simple string join for S3 to avoid OS-specific separators
            file_path = f"{data_path.rstrip('/')}/{file_name}"
            path_check = True # Cannot easily check existence on S3 without boto3
        else:
            file_path = os.path.join(data_path, file_name)
            path_check = os.path.exists(file_path)

        if path_check:
            try:
                # DuckDB can read parquet directories directly using glob syntax or just path
                query = f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{file_path}/*.parquet')"
                con.execute(query)
                loaded_tables.append(table_name)
            except Exception as e:
                # Only show error if we expected a local file, otherwise it might just be missing from S3
                if not is_remote:
                    st.error(f"Error loading {table_name}: {e}")
    return loaded_tables

def get_schema_string(con, tables):
    schema_str = ""
    for table in tables:
        schema_str += f"Table: {table}\nColumns:\n"
        # Get columns for the table
        columns = con.execute(f"DESCRIBE {table}").fetchall()
        for col in columns:
            schema_str += f"- {col[0]} ({col[1]})\n"
        schema_str += "\n"
    return schema_str

def generate_sql(user_query, schema_str, api_key):
    if not api_key:
        return "Error: DeepSeek API Key is missing."
    
    # Configure for DeepSeek API
    # DeepSeek is OpenAI-compatible, so we can use ChatOpenAI with the correct base_url
    llm = ChatOpenAI(
        model="deepseek-chat", 
        temperature=0, 
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    
    template = """You are an expert SQL analyst using DuckDB.
    Your task is to generate a valid DuckDB SQL query to answer the user's question based on the provided schema.
    
    Schema:
    {schema}
    
    User Question: {question}
    
    Constraints:
    1. Return ONLY the SQL query. Do not include markdown formatting (like ```sql).
    2. Use Common Table Expressions (CTEs) for readability if the query is complex.
    3. Ensure column names match the schema exactly.
    4. If the question cannot be answered with the available schema, return "I cannot answer this question with the available data."
    
    SQL Query:
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    
    try:
        return chain.invoke({"schema": schema_str, "question": user_query})
    except Exception as e:
        return f"Error generating SQL: {e}"

def main():
    st.set_page_config(page_title="KaggleMind", layout="wide")
    st.title("KaggleMind: Agentic SQL Analyst")
    
    # Sidebar for setup
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("DeepSeek API Key", type="password")
        if not api_key:
            st.warning("Please enter your DeepSeek API Key to use the agent.")
            
        st.header("System Status")
        con = get_connection()
        
        if st.button("Reload Data"):
            # Allow overriding data path via env var for S3 usage
            data_source = os.getenv("DATA_PATH", "data/processed")
            with st.spinner("Loading data into DuckDB..."):
                loaded_tables = load_data_into_duckdb(con, data_path=data_source)
                if loaded_tables:
                    st.success(f"Loaded tables: {', '.join(loaded_tables)}")
                    st.session_state['loaded_tables'] = loaded_tables
                else:
                    st.error("Processed data not found. Run the pipeline first.")
        
        if 'loaded_tables' in st.session_state:
            st.write("Active Tables:", st.session_state['loaded_tables'])

    # Main Chat Interface
    st.subheader("Ask a question about the Kaggle dataset")
    user_query = st.text_input("Query", "How many competitions are there for each host segment? Can you show me the top 10?")
    # example question: "Which Kaggle Grandmasters have the highest conversion rate from forum posts to competition gold medals?"

    if st.button("Analyze"):
        if not api_key:
            st.error("Please provide a DeepSeek API Key in the sidebar.")
            return

        if 'loaded_tables' not in st.session_state or not st.session_state['loaded_tables']:
            st.error("Please load data first using the sidebar button.")
            return

        st.info("Agent is thinking...")
        
        # 1. Get Schema
        schema_str = get_schema_string(con, st.session_state['loaded_tables'])
        
        # 2. Generate SQL
        generated_sql = generate_sql(user_query, schema_str, api_key)
        
        # Clean up SQL if it contains markdown
        generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
        
        st.markdown("### Generated SQL")
        st.code(generated_sql, language="sql")
        
        if "Error" in generated_sql or "cannot answer" in generated_sql:
            st.error(generated_sql)
        else:
            # 3. Execute SQL
            try:
                df = con.execute(generated_sql).df()
                st.markdown("### Results")
                st.dataframe(df)
                
                if not df.empty:
                    # Simple auto-visualization logic
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0 and len(df.columns) > 1:
                        # Pick the first non-numeric column as X (if exists) and first numeric as Y
                        non_numeric_cols = df.select_dtypes(exclude=['number']).columns
                        x_col = non_numeric_cols[0] if len(non_numeric_cols) > 0 else df.columns[0]
                        y_col = numeric_cols[0]
                        
                        st.markdown("### Visualization")
                        fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
                        st.plotly_chart(fig)
            except Exception as e:
                st.error(f"Error executing SQL: {e}")

if __name__ == "__main__":
    main()
