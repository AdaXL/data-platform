import streamlit as st
import pandas as pd
import os

def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return None

def main():
    st.title("Meta Kaggle Dataset Explorer")

    data_path = 'data/raw' # Assumes data is downloaded here
    
    if not os.path.exists(data_path):
        st.error(f"Data directory '{data_path}' not found. Please download the dataset first using 'python src/ingestion/kaggle_downloader.py'.")
        return

    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    
    if not files:
        st.warning(f"No CSV files found in '{data_path}'.")
        return

    st.sidebar.header("Settings")
    selected_file = st.sidebar.selectbox("Select a file to explore", files)
    
    if selected_file:
        file_path = os.path.join(data_path, selected_file)
        st.write(f"### {selected_file} Preview")
        
        try:
            # Read only first few rows to avoid memory issues with large files
            df = pd.read_csv(file_path, nrows=100)
            st.dataframe(df)
            
            st.write("### Basic Information")
            st.write(f"**Columns:** {list(df.columns)}")
            
            if st.checkbox("Show Summary Statistics"):
                st.write(df.describe())
                
        except Exception as e:
            st.error(f"Error loading file: {e}")

if __name__ == "__main__":
    main()
