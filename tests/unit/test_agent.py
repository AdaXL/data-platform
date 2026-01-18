import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from agent.graph import SQLAgent


class TestSQLAgent(unittest.TestCase):

    @patch("agent.graph.SchemaRetriever")
    @patch("agent.graph.ChatOpenAI")
    def test_agent_workflow(self, mock_chat_openai, mock_retriever):
        # Setup mocks
        mock_con = MagicMock()
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm

        # Mock Retriever
        mock_retriever_instance = mock_retriever.return_value
        mock_retriever_instance.retrieve_relevant_tables.return_value = ["users"]

        # Mock LLM responses for the chain
        # We need to mock the chain invocation.
        # Since the code uses chain = prompt | llm | parser, we mock the chain execution flow or just the llm invocation if possible.
        # However, LangChain's pipe syntax makes mocking tricky.
        # A simpler way is to mock the `invoke` method of the compiled graph if we just want to test the run method,
        # but here we want to test the logic.

        # Let's mock the internal methods of SQLAgent to test the flow logic without relying on actual LangChain execution
        agent = SQLAgent(mock_con, "fake_key")

        # Mock the graph invocation
        agent.workflow = MagicMock()
        expected_result = {
            "sql_query": "SELECT * FROM users",
            "query_result": pd.DataFrame(),
            "error": None,
        }
        agent.workflow.invoke.return_value = expected_result

        # Run
        result = agent.run("Test question")

        # Assert
        agent.workflow.invoke.assert_called_with({"question": "Test question"})
        self.assertEqual(result, expected_result)


if __name__ == "__main__":
    unittest.main()
