import json

import pandas as pd
import plotly.express as px
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


class VisualizationAgent:
    def __init__(
        self, api_key, base_url="https://api.deepseek.com", model="deepseek-chat"
    ):
        self.llm = ChatOpenAI(
            model=model, temperature=0, api_key=api_key, base_url=base_url
        )

    def suggest_visualization(self, df: pd.DataFrame, query: str):
        """
        Analyzes the DataFrame and user query to suggest the best Plotly visualization.
        Returns a dictionary with 'chart_type' and 'params'.
        """
        if df.empty:
            return None

        # Prepare context for the LLM
        columns_info = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            sample_values = df[col].head(3).tolist()
            columns_info.append(f"- {col} ({dtype}): e.g., {sample_values}")

        columns_str = "\n".join(columns_info)

        template = """You are a data visualization expert using Plotly Express.
        Your task is to choose the most suitable chart type and parameters to visualize the provided data based on the user's query.

        User Query: {query}

        Data Schema & Samples:
        {columns_info}

        Available Plotly Express Chart Types:
        - bar (for comparisons, rankings, distributions)
        - line (for trends over time, continuous data)
        - scatter (for correlations, relationships)
        - pie (for part-to-whole comparisons, use sparingly)
        - histogram (for frequency distributions)
        - box (for statistical distribution, outliers)

        Instructions:
        1. Analyze the data columns and the user's intent.
        2. Select the best chart type.
        3. Map the DataFrame columns to the chart parameters (x, y, color, etc.).
        4. Provide a suitable title.
        5. Return ONLY a valid JSON object. Do not include markdown formatting.

        JSON Structure:
        {{
            "chart_type": "bar",
            "params": {{
                "x": "column_name",
                "y": "column_name",
                "color": "column_name (optional)",
                "title": "Chart Title"
            }},
            "reasoning": "Brief explanation of why this chart was chosen."
        }}
        """

        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()

        try:
            response = chain.invoke({"query": query, "columns_info": columns_str})
            clean_json = response.replace("```json", "").replace("```", "").strip()
            config = json.loads(clean_json)
            return config
        except Exception as e:
            print(f"Error generating visualization config: {e}")
            return self._fallback_visualization(df)

    def create_chart(self, df: pd.DataFrame, config: dict):
        """
        Attempts to create a chart based on config.
        If it fails, it tries to self-correct by falling back to a simpler chart.
        """
        try:
            chart_type = config.get("chart_type")
            params = config.get("params", {})

            if chart_type and hasattr(px, chart_type):
                return getattr(px, chart_type)(df, **params)
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")

        except Exception as e:
            print(f"Visualization error: {e}. Attempting self-correction...")
            return self._create_fallback_chart(df)

    def _fallback_visualization(self, df: pd.DataFrame):
        """
        Generates a safe default configuration if the LLM fails.
        """
        numeric_cols = df.select_dtypes(include=["number"]).columns
        non_numeric_cols = df.select_dtypes(exclude=["number"]).columns

        if len(numeric_cols) > 0 and len(non_numeric_cols) > 0:
            return {
                "chart_type": "bar",
                "params": {
                    "x": non_numeric_cols[0],
                    "y": numeric_cols[0],
                    "title": f"{numeric_cols[0]} by {non_numeric_cols[0]} (Fallback)",
                },
                "reasoning": "Fallback: Bar chart of first numeric vs first categorical column.",
            }
        elif len(numeric_cols) >= 2:
            return {
                "chart_type": "scatter",
                "params": {
                    "x": numeric_cols[0],
                    "y": numeric_cols[1],
                    "title": f"{numeric_cols[1]} vs {numeric_cols[0]} (Fallback)",
                },
                "reasoning": "Fallback: Scatter plot of two numeric columns.",
            }
        else:
            return None

    def _create_fallback_chart(self, df: pd.DataFrame):
        """
        Directly creates a Plotly figure using safe defaults.
        """
        config = self._fallback_visualization(df)
        if config:
            try:
                chart_type = config["chart_type"]
                params = config["params"]
                return getattr(px, chart_type)(df, **params)
            except:
                return None
        return None
