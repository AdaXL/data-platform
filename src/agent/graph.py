from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import duckdb
import pandas as pd

from agent.rag_retriever import SchemaRetriever

# Define the Agent State
class AgentState(TypedDict):
    question: str
    schema_context: str
    relevant_tables: List[str]
    sql_query: str
    query_result: Union[str, pd.DataFrame]
    error: str
    attempts: int

class SQLAgent:
    def __init__(self, connection, api_key, base_url="https://api.deepseek.com", model="deepseek-chat"):
        self.con = connection
        self.retriever = SchemaRetriever()
        self.llm = ChatOpenAI(
            model=model,
            temperature=0,
            api_key=api_key,
            base_url=base_url
        )
        self.workflow = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # Define Nodes
        workflow.add_node("retrieve", self.retrieve_node)
        workflow.add_node("generate", self.generate_node)
        workflow.add_node("execute", self.execute_node)
        workflow.add_node("correct", self.correct_node)

        # Define Edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", "execute")
        
        # Conditional Edge based on execution result
        workflow.add_conditional_edges(
            "execute",
            self.check_execution,
            {
                "success": END,
                "error": "correct"
            }
        )
        
        workflow.add_edge("correct", "execute") # Loop back to execution

        return workflow.compile()

    def retrieve_node(self, state: AgentState):
        tables = self.retriever.retrieve_relevant_tables(state["question"])
        
        # Build schema string only for relevant tables
        schema_str = ""
        for table in tables:
            try:
                columns = self.con.execute(f"DESCRIBE {table}").fetchall()
                schema_str += f"Table: {table}\nColumns:\n"
                for col in columns:
                    schema_str += f"- {col[0]} ({col[1]})\n"
                schema_str += "\n"
            except:
                pass # Table might not be loaded
        
        return {"relevant_tables": tables, "schema_context": schema_str, "attempts": 0}

    def generate_node(self, state: AgentState):
        # Few-shot examples to "fine-tune" the agent's understanding of the schema
        examples = """
        Examples:
        
        Question: "List the top 5 users with the most gold medals in Competitions."
        SQL:
        SELECT u.DisplayName, ua.TotalGold
        FROM users u
        JOIN user_achievements ua ON u.Id = ua.UserId
        WHERE ua.AchievementType = 'Competitions'
        ORDER BY ua.TotalGold DESC
        LIMIT 5;

        Question: "How many forum posts does each Grandmaster have on average?"
        SQL:
        WITH GMs AS (
            SELECT UserId
            FROM user_achievements
            WHERE AchievementType = 'Competitions' AND Tier = 4
        ),
        PostCounts AS (
            SELECT PostUserId, COUNT(*) as PostCount
            FROM forum_messages
            GROUP BY PostUserId
        )
        SELECT AVG(pc.PostCount) as AvgPosts
        FROM GMs
        JOIN PostCounts pc ON GMs.UserId = pc.PostUserId;
        """

        template = """You are an expert SQL analyst using DuckDB.
        Your task is to generate a valid DuckDB SQL query to answer the user's question based on the provided schema.
        
        Schema:
        {schema}
        
        {examples}
        
        User Question: {question}
        
        Constraints:
        1. Return ONLY the SQL query. Do not include markdown formatting (like ```sql).
        2. Use Common Table Expressions (CTEs) for readability if the query is complex.
        3. Ensure column names match the schema exactly.
        4. If the question cannot be answered with the available schema, return "I cannot answer this question with the available data."
        
        SQL Query:
        """
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        sql = chain.invoke({
            "schema": state["schema_context"], 
            "question": state["question"],
            "examples": examples
        })
        clean_sql = sql.replace("```sql", "").replace("```", "").strip()
        return {"sql_query": clean_sql}

    def execute_node(self, state: AgentState):
        try:
            df = self.con.execute(state["sql_query"]).df()
            return {"query_result": df, "error": None}
        except Exception as e:
            return {"error": str(e), "query_result": None}

    def correct_node(self, state: AgentState):
        state["attempts"] += 1
        if state["attempts"] > 3:
            return {"sql_query": "SELECT 'Max retries exceeded' as error"} # Break loop
            
        template = """The previous SQL query failed. Fix it based on the error.
        
        Schema:
        {schema}
        
        Previous SQL:
        {sql}
        
        Error Message:
        {error}
        
        Constraints:
        1. Return ONLY the corrected SQL query. Do not include markdown formatting (like ```sql).
        2. Ensure column names match the schema exactly.
        3. Use Common Table Expressions (CTEs) for readability.
        
        Corrected SQL Query:
        """
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        fixed_sql = chain.invoke({
            "schema": state["schema_context"], 
            "sql": state["sql_query"],
            "error": state["error"]
        })
        clean_sql = fixed_sql.replace("```sql", "").replace("```", "").strip()
        return {"sql_query": clean_sql}

    def check_execution(self, state: AgentState):
        if state["error"] is None:
            return "success"
        if state["attempts"] > 3:
            return "success" # Force exit to avoid infinite loop
        return "error"

    def run(self, question: str):
        return self.workflow.invoke({"question": question})
