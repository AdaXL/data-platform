import json

import pandas as pd
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

            # Clean up response if it contains markdown
            clean_json = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception as e:
            print(f"Error generating visualization config: {e}")
            return None
