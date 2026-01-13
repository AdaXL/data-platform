import streamlit as st
import pandas as pd
import duckdb
import os
import plotly.express as px

# Initialize DuckDB connection
@st.cache_resource
def get_connection():
    con = duckdb.connect(database=':memory:')
    return con

def load_data_into_duckdb(con, data_path='data/processed'):
    """
    Loads Parquet files from the processed directory into DuckDB tables.
    """
    if not os.path.exists(data_path):
        return False
    
    tables = {
        'users': 'users',
        'competitions': 'competitions',
        'user_achievements': 'user_achievements',
        'forum_messages': 'forum_messages',
        'user_followers': 'user_followers'
    }
    
    for table_name, file_name in tables.items():
        file_path = os.path.join(data_path, file_name) # Parquet is a directory or file
        # Check if directory exists (Spark writes parquet as directory)
        if os.path.exists(file_path):
            try:
                # DuckDB can read parquet directories directly using glob syntax or just path
                query = f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{file_path}/*.parquet')"
                con.execute(query)
            except Exception as e:
                st.error(f"Error loading {table_name}: {e}")
    return True

def main():
    st.set_page_config(page_title="KaggleMind", layout="wide")
    st.title("KaggleMind: Agentic SQL Analyst")
    
    con = get_connection()
    
    # Sidebar for setup
    with st.sidebar:
        st.header("System Status")
        if st.button("Reload Data"):
            with st.spinner("Loading data into DuckDB..."):
                success = load_data_into_duckdb(con)
                if success:
                    st.success("Data loaded successfully!")
                else:
                    st.error("Processed data not found. Run the pipeline first.")
        
        st.header("Schema Info")
        if st.checkbox("Show Tables"):
            tables = con.execute("SHOW TABLES").fetchall()
            st.write([t[0] for t in tables])

    # Main Chat Interface
    st.subheader("Ask a question about the Kaggle dataset")
    user_query = st.text_input("Query", "Which Kaggle Grandmasters have the highest conversion rate from forum posts to competition gold medals?")
    
    if st.button("Analyze"):
        st.info("Agent is thinking... (Mock implementation for now)")
        
        # Placeholder for Agent Logic
        # In a real implementation, this would call the LangGraph agent
        
        # Mock SQL generation for demonstration
        st.markdown("### Agent Thought Trace")
        st.markdown("""
        1. **Planner**: Identified need for `Users`, `UserAchievements`, and `ForumMessages`.
        2. **Coder**: Generating SQL to join these tables and calculate conversion rate.
        """)
        
        mock_sql = """
        -- This is a placeholder SQL query
        SELECT 
            u.DisplayName,
            COUNT(DISTINCT fm.Id) as ForumPosts,
            SUM(CASE WHEN ua.AchievementType = 'Competitions' AND ua.Tier = 4 THEN 1 ELSE 0 END) as GoldMedals
        FROM users u
        JOIN user_achievements ua ON u.Id = ua.UserId
        LEFT JOIN forum_messages fm ON u.Id = fm.PostUserId
        WHERE ua.Tier = 4 -- Grandmaster
        GROUP BY u.DisplayName
        HAVING ForumPosts > 0
        ORDER BY GoldMedals DESC
        LIMIT 10
        """
        
        st.code(mock_sql, language="sql")
        
        try:
            # Execute mock SQL (might fail if tables aren't actually loaded with correct schema)
            # For now, let's just show a sample dataframe if query fails or tables missing
            try:
                df = con.execute(mock_sql).df()
                st.dataframe(df)
                
                if not df.empty:
                    fig = px.bar(df, x='DisplayName', y='GoldMedals', title="Top Grandmasters by Gold Medals")
                    st.plotly_chart(fig)
            except Exception as e:
                st.warning(f"Could not execute generated SQL against current data: {e}")
                st.info("Displaying mock data for visualization:")
                
                mock_data = pd.DataFrame({
                    'DisplayName': ['GM_A', 'GM_B', 'GM_C'],
                    'ForumPosts': [150, 300, 50],
                    'GoldMedals': [10, 8, 5]
                })
                st.dataframe(mock_data)
                fig = px.bar(mock_data, x='DisplayName', y='GoldMedals', title="Top Grandmasters by Gold Medals (Mock)")
                st.plotly_chart(fig)

        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
