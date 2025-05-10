#!/usr/bin/env python3
"""
Unit tests for scholar_agent.py module.

This test module focuses on testing the functionality of the ScholarAgent class and its
helper classes like ChromaDBTool and CohereReranker.
"""

import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
from pathlib import Path
import pytest
import json
import os

# Add the parent directory to the path to import the module
current_file = Path(__file__)
parent_dir = current_file.parent.parent.parent
sys.path.append(str(parent_dir))

# Mock all required modules before importing scholar_agent
sys.modules["langgraph"] = MagicMock()
sys.modules["langgraph.graph"] = MagicMock()
sys.modules["langgraph.graph"].StateGraph = MagicMock()
sys.modules["langgraph.graph"].END = "END"
sys.modules["langchain_core"] = MagicMock()
sys.modules["langchain_core.messages"] = MagicMock()
sys.modules["langchain_core.messages"].AnyMessage = MagicMock
sys.modules["langchain_core.messages"].SystemMessage = MagicMock
sys.modules["langchain_core.messages"].HumanMessage = MagicMock
sys.modules["langchain_core.messages"].ToolMessage = MagicMock
sys.modules["langchain_openai"] = MagicMock()
sys.modules["langchain_openai"].ChatOpenAI = MagicMock


# Create actual mock message classes for testing
class MockHumanMessage:
    def __init__(self, content):
        self.content = content


# Now patch the actual classes before importing
sys.modules["langchain_core.messages"].HumanMessage = MockHumanMessage

# Import after mocking dependencies
with patch("agent.scholar_agent.ChromaDBManager"):
    from agent.scholar_agent import (
        get_openai_api_key,
        ChromaDBTool,
        CohereReranker,
        ScholarAgent,
        create_scholar_agent,
        AgentState,
    )


class TestScholarAgentModuleFunctions(unittest.TestCase):
    """Test helper functions in the scholar_agent module."""

    @patch("agent.scholar_agent.Path.exists", return_value=True)
    @patch("agent.scholar_agent.load_dotenv")
    @patch("agent.scholar_agent.os.getenv", return_value="fake-api-key")
    def test_get_openai_api_key(self, mock_getenv, mock_load_dotenv, mock_exists):
        """Test get_openai_api_key retrieves the API key correctly."""
        api_key = get_openai_api_key()
        self.assertEqual(api_key, "fake-api-key")
        mock_load_dotenv.assert_called_once()
        mock_getenv.assert_called_once_with("OPENAI_API_KEY")

    @patch("agent.scholar_agent.Path.exists", return_value=False)
    def test_get_openai_api_key_file_not_found(self, mock_exists):
        """Test get_openai_api_key raises FileNotFoundError when env file doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            get_openai_api_key()

    @patch("agent.scholar_agent.Path.exists", return_value=True)
    @patch("agent.scholar_agent.load_dotenv")
    @patch("agent.scholar_agent.os.getenv", return_value=None)
    def test_get_openai_api_key_missing_key(self, mock_getenv, mock_load_dotenv, mock_exists):
        """Test get_openai_api_key raises ValueError when API key is not set."""
        with self.assertRaises(ValueError):
            get_openai_api_key()

    @patch("agent.scholar_agent.get_openai_api_key", return_value="fake-api-key")
    @patch("agent.scholar_agent.ScholarAgent")
    def test_create_scholar_agent(self, mock_scholar_agent, mock_get_api_key):
        """Test create_scholar_agent function."""
        # Setup mock
        mock_agent_instance = MagicMock()
        mock_scholar_agent.return_value = mock_agent_instance

        # Create a mock tool for testing
        mock_tool = MagicMock()
        mock_tool.name = "chromadb_search"

        # Test with tools parameter
        agent = create_scholar_agent(tools=[mock_tool])

        # Verify ScholarAgent was created with expected arguments
        mock_get_api_key.assert_called_once()
        mock_scholar_agent.assert_called_once_with(api_key="fake-api-key", tools=[mock_tool], system="")
        self.assertEqual(agent, mock_agent_instance)


class TestChromaDBTool(unittest.TestCase):
    """Test the ChromaDBTool class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "fake-api-key"
        self.db_manager_patch = patch("agent.scholar_agent.ChromaDBManager")
        self.mock_db_manager = self.db_manager_patch.start()
        self.mock_db_instance = MagicMock()
        self.mock_db_manager.return_value = self.mock_db_instance

    def tearDown(self):
        """Tear down test fixtures."""
        self.db_manager_patch.stop()

    def test_init(self):
        """Test initialization of ChromaDBTool."""
        tool = ChromaDBTool(self.api_key, n_results=200)
        self.assertEqual(tool.name, "chromadb_search")
        self.assertEqual(tool.api_key, self.api_key)
        self.assertEqual(tool.n_results, 200)
        self.mock_db_manager.assert_called_once_with(collection_name="google_scholar", n_results=200)

    def test_invoke(self):
        """Test the invoke method queries ChromaDB correctly."""
        # Setup mock return value
        self.mock_db_instance.query.return_value = [{"text": "test article"}]

        # Create tool and call invoke
        tool = ChromaDBTool(self.api_key)
        result = tool.invoke("query", n_results=10)

        # Verify the result and that ChromaDBManager query was called
        self.assertEqual(result, [{"text": "test article"}])
        self.mock_db_instance.query.assert_called_once_with("query", n_results=10)

    def test_invoke_exception(self):
        """Test that exceptions are properly raised from the invoke method."""
        # Setup mock to raise an exception
        self.mock_db_instance.query.side_effect = Exception("Database error")

        # Create tool and call invoke, expecting exception
        tool = ChromaDBTool(self.api_key)
        with self.assertRaises(RuntimeError) as context:
            tool.invoke("query")

        self.assertIn("Failed to query ChromaDB: Database error", str(context.exception))


class TestCohereReranker(unittest.TestCase):
    """Test the CohereReranker class."""

    @patch("agent.scholar_agent.os.getenv", return_value="fake-cohere-key")
    @patch("agent.scholar_agent.cohere.Client")
    def test_init_with_key(self, mock_client, mock_getenv):
        """Test initialization with a valid API key."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        reranker = CohereReranker()

        self.assertEqual(reranker.name, "cohere_reranker")
        self.assertEqual(reranker.api_key, "fake-cohere-key")
        self.assertEqual(reranker.client, mock_client_instance)
        mock_getenv.assert_called_once_with("COHERE_API_KEY")
        mock_client.assert_called_once_with("fake-cohere-key")

    @patch("agent.scholar_agent.os.getenv", return_value=None)
    def test_init_without_key(self, mock_getenv):
        """Test initialization without an API key."""
        reranker = CohereReranker()

        self.assertEqual(reranker.name, "cohere_reranker")
        self.assertIsNone(reranker.api_key)
        self.assertIsNone(reranker.client)
        mock_getenv.assert_called_once_with("COHERE_API_KEY")

    @patch("agent.scholar_agent.os.getenv", return_value="fake-cohere-key")
    @patch("agent.scholar_agent.cohere.Client")
    def test_init_with_client_error(self, mock_client, mock_getenv):
        """Test handling of client initialization error."""
        mock_client.side_effect = Exception("Client error")

        reranker = CohereReranker()

        self.assertEqual(reranker.name, "cohere_reranker")
        self.assertEqual(reranker.api_key, "fake-cohere-key")
        self.assertIsNone(reranker.client)
        mock_getenv.assert_called_once_with("COHERE_API_KEY")
        mock_client.assert_called_once_with("fake-cohere-key")

    @patch("agent.scholar_agent.os.getenv", return_value=None)
    def test_rerank_fallback_scoring(self, mock_getenv):
        """Test fallback scoring when Cohere client is not available."""
        reranker = CohereReranker()

        documents = [
            {"text": "This is about deep learning and neural networks"},
            {"text": "This document is about something else"},
        ]

        results = reranker.rerank("deep learning", documents)

        # Expect the first document to have higher score as it contains the query
        self.assertEqual(len(results), 2)
        self.assertGreater(results[0]["score"], results[1]["score"])
        self.assertEqual(results[0]["document"], documents[0])

    @patch("agent.scholar_agent.os.getenv", return_value="fake-cohere-key")
    @patch("agent.scholar_agent.cohere.Client")
    def test_rerank_with_cohere(self, mock_client, mock_getenv):
        """Test reranking with Cohere API."""
        mock_client_instance = MagicMock()
        mock_response = MagicMock()

        # Setup mock results
        result1 = MagicMock()
        result1.relevance_score = 0.9
        result2 = MagicMock()
        result2.relevance_score = 0.5
        mock_response.results = [result1, result2]
        mock_client_instance.rerank.return_value = mock_response
        mock_client.return_value = mock_client_instance

        reranker = CohereReranker()

        documents = [
            {"text": "This is about deep learning and neural networks"},
            {"text": "This document is about something else"},
        ]

        results = reranker.rerank("deep learning", documents)

        # Verify results and that Cohere API was called
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["score"], 0.9)
        self.assertEqual(results[1]["score"], 0.5)
        self.assertEqual(results[0]["document"], documents[0])
        self.assertEqual(results[1]["document"], documents[1])
        mock_client_instance.rerank.assert_called_once()

    @patch("agent.scholar_agent.os.getenv", return_value="fake-cohere-key")
    @patch("agent.scholar_agent.cohere.Client")
    def test_rerank_with_cohere_error(self, mock_client, mock_getenv):
        """Test handling of Cohere API error."""
        mock_client_instance = MagicMock()
        mock_client_instance.rerank.side_effect = Exception("API error")
        mock_client.return_value = mock_client_instance

        reranker = CohereReranker()

        documents = [{"text": "Document 1"}, {"text": "Document 2"}]

        results = reranker.rerank("query", documents)

        # Should have uniform fallback scores
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["score"], 0.5)
        self.assertEqual(results[1]["score"], 0.5)
        mock_client_instance.rerank.assert_called_once()


@patch("agent.scholar_agent.StateGraph")
@patch("agent.scholar_agent.ChatOpenAI")
class TestScholarAgent(unittest.TestCase):
    """Test the ScholarAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "fake-api-key"
        self.mock_tools = [MagicMock(), MagicMock()]
        self.mock_tools[0].name = "tool1"
        self.mock_tools[1].name = "tool2"

    def test_init(self, mock_chat_openai, mock_state_graph):
        """Test initialization of ScholarAgent."""
        # Setup mocks
        mock_chat_instance = MagicMock()
        mock_chat_openai.return_value = mock_chat_instance
        mock_graph_instance = MagicMock()
        mock_state_graph.return_value = mock_graph_instance

        # Create agent
        agent = ScholarAgent(self.api_key, tools=self.mock_tools)

        # Verify initialization
        self.assertEqual(agent.api_key, self.api_key)

        # Check that tools were converted to a dictionary with name as the key
        self.assertIsInstance(agent.tools, dict)
        self.assertIn("tool1", agent.tools)
        self.assertIn("tool2", agent.tools)
        self.assertEqual(agent.tools["tool1"], self.mock_tools[0])
        self.assertEqual(agent.tools["tool2"], self.mock_tools[1])

        # Check with the correct model parameter
        mock_chat_openai.assert_called_once_with(model="gpt-4", api_key=self.api_key)
        mock_state_graph.assert_called_once()
        self.assertIsNotNone(agent.graph)

    def test_parse_interests(self, mock_chat_openai, mock_state_graph):
        """Test _parse_interests method (private method)."""
        # Setup mocks
        mock_state_graph_instance = MagicMock()
        mock_state_graph.return_value = mock_state_graph_instance
        mock_chat_instance = MagicMock()
        mock_chat_openai.return_value = mock_chat_instance

        # Create agent
        agent = ScholarAgent(self.api_key, tools=self.mock_tools)

        # Test with comma-separated interests
        interests_str = "Machine Learning, Natural Language Processing, Deep Learning"
        interests = agent._parse_interests(interests_str)
        self.assertEqual(interests, ["Machine Learning", "Natural Language Processing", "Deep Learning"])

        # Test with semicolon-separated interests
        interests_str = "Machine Learning; Natural Language Processing; Deep Learning"
        interests = agent._parse_interests(interests_str)
        self.assertEqual(interests, ["Machine Learning", "Natural Language Processing", "Deep Learning"])

        # Test with pipe-separated interests
        interests_str = "Machine Learning | Natural Language Processing | Deep Learning"
        interests = agent._parse_interests(interests_str)
        self.assertEqual(interests, ["Machine Learning", "Natural Language Processing", "Deep Learning"])

        # Test with a single interest (no delimiter)
        interests_str = "Artificial Intelligence"
        interests = agent._parse_interests(interests_str)
        self.assertEqual(interests, ["Artificial Intelligence"])

        # Test with an empty string
        interests = agent._parse_interests("")
        self.assertEqual(interests, [])

        # Test with None
        interests = agent._parse_interests(None)
        self.assertEqual(interests, [])

        # Test with a list already
        interests = agent._parse_interests(["Machine Learning", "Deep Learning"])
        self.assertEqual(interests, ["Machine Learning", "Deep Learning"])

    @patch("agent.scholar_agent.print")
    def test_retrieve_articles(self, mock_print, mock_chat_openai, mock_state_graph):
        """Test retrieve_articles method."""
        # Setup mocks
        mock_state_graph_instance = MagicMock()
        mock_state_graph.return_value = mock_state_graph_instance
        mock_chat_instance = MagicMock()
        mock_chat_openai.return_value = mock_chat_instance

        # Setup mock tool with different response patterns for different query phases
        mock_chroma_tool = MagicMock()
        mock_chroma_tool.name = "chromadb_search"

        # Set up the invoke method to return different results based on the query
        def mock_invoke(query, n_results=None):
            if query == "machine learning":  # Phase 1: Direct search
                return [
                    {"metadata": {"doc_type": "author", "author": "Prof A"}, "content": "Expert in machine learning"}
                ]
            elif "doc_type:author AND" in query:  # Phase 2: Author-specific search
                return []
            return []

        mock_chroma_tool.invoke = MagicMock(side_effect=mock_invoke)

        # Create agent with the mock tool
        agent = ScholarAgent(self.api_key, tools=[mock_chroma_tool])

        # Test retrieve_articles
        state = {"messages": [MockHumanMessage("machine learning")]}
        new_state = agent.retrieve_articles(state)

        # Verify the state was updated with messages
        self.assertIn("messages", new_state)
        self.assertEqual(len(new_state["messages"]), 1)

        # Mock should be called multiple times with different queries
        # But we can't predict exactly how many times due to implementation details
        mock_chroma_tool.invoke.assert_called()

        # The message content should not be an empty list string
        self.assertNotEqual(new_state["messages"][0].content, "[]")

    @patch("agent.scholar_agent.print")
    def test_retrieve_articles_empty_results(self, mock_print, mock_chat_openai, mock_state_graph):
        """Test retrieve_articles method with empty results."""
        # Setup mocks
        mock_state_graph_instance = MagicMock()
        mock_state_graph.return_value = mock_state_graph_instance
        mock_chat_instance = MagicMock()
        mock_chat_openai.return_value = mock_chat_instance

        # Setup mock tool that returns empty results for all queries
        mock_chroma_tool = MagicMock()
        mock_chroma_tool.name = "chromadb_search"
        mock_chroma_tool.invoke.return_value = []

        # Create agent with the mock tool
        agent = ScholarAgent(self.api_key, tools=[mock_chroma_tool])

        # Test retrieve_articles
        state = {"messages": [MockHumanMessage("machine learning")]}
        new_state = agent.retrieve_articles(state)

        # Verify empty results handling
        self.assertIn("messages", new_state)
        self.assertEqual(len(new_state["messages"]), 1)
        self.assertEqual(new_state["messages"][0].content, "[]")  # Empty results should return "[]"

        # Check that the tool was called with the expected query
        # The actual implementation will make multiple calls
        mock_chroma_tool.invoke.assert_any_call("machine learning", n_results=100)

    @patch("agent.scholar_agent.print")
    def test_retrieve_articles_exception(self, mock_print, mock_chat_openai, mock_state_graph):
        """Test retrieve_articles method handling exceptions."""
        # Setup mocks
        mock_state_graph_instance = MagicMock()
        mock_state_graph.return_value = mock_state_graph_instance
        mock_chat_instance = MagicMock()
        mock_chat_openai.return_value = mock_chat_instance

        # Setup mock tool that raises an exception
        mock_chroma_tool = MagicMock()
        mock_chroma_tool.name = "chromadb_search"
        mock_chroma_tool.invoke.side_effect = Exception("Database error")

        # Create agent with the mock tool
        agent = ScholarAgent(self.api_key, tools=[mock_chroma_tool])

        # Test retrieve_articles
        state = {"messages": [MockHumanMessage("machine learning")]}
        new_state = agent.retrieve_articles(state)

        # Verify exception handling
        self.assertIn("messages", new_state)
        self.assertEqual(len(new_state["messages"]), 1)
        self.assertEqual(new_state["messages"][0].content, "[]")  # Exception should return "[]"
        mock_chroma_tool.invoke.assert_called()

        # Check that error was printed, but we can't check the exact arguments
        # because the implementation might include traceback or other details
        mock_print_calls = [call_args[0][0] for call_args in mock_print.call_args_list if len(call_args[0]) > 0]
        self.assertTrue(
            any("Error retrieving articles" in str(call) for call in mock_print_calls), "No error message was printed"
        )

    @patch("agent.scholar_agent.print")
    def test_rerank_articles(self, mock_print, mock_chat_openai, mock_state_graph):
        """Test rerank_articles method."""
        # Setup mocks
        mock_state_graph_instance = MagicMock()
        mock_state_graph.return_value = mock_state_graph_instance
        mock_chat_instance = MagicMock()
        mock_chat_openai.return_value = mock_chat_instance

        # Setup mock reranker
        mock_reranker = MagicMock()
        mock_reranker.name = "cohere_reranker"
        mock_reranker.rerank.return_value = [
            {"document": {"text": "Article about machine learning by Professor A"}, "score": 0.9},
            {"document": {"text": "Article about deep learning by Professor B"}, "score": 0.5},
        ]

        # Create agent with the mock reranker
        agent = ScholarAgent(self.api_key, tools=[mock_reranker])
        agent.reranker = mock_reranker  # Directly set the reranker

        # Construct a realistic state with formatted results
        formatted_results = [
            {
                "author_profile": {"metadata": {"author": "Professor A"}},
                "website_content": [{"text": "Article about machine learning by Professor A"}],
                "journal_content": [{"text": "Journal article by Professor A"}],
            }
        ]

        # Create the input state as expected by rerank_articles
        state = {
            "messages": [
                MockHumanMessage("machine learning"),  # Original query
                MockHumanMessage(str(formatted_results)),  # Results from retrieve_articles
            ]
        }

        # Test rerank_articles
        new_state = agent.rerank_articles(state)

        # Verify the state contains a messages key with HumanMessage
        self.assertIn("messages", new_state)
        self.assertEqual(len(new_state["messages"]), 1)

        # The message should not be empty
        self.assertNotEqual(new_state["messages"][0].content, "[]")

        # Reranker should have been called for website_content and journal_content
        self.assertEqual(mock_reranker.rerank.call_count, 2)

    @patch("agent.scholar_agent.print")
    def test_rerank_articles_empty_results(self, mock_print, mock_chat_openai, mock_state_graph):
        """Test rerank_articles method with empty results."""
        # Setup mocks
        mock_state_graph_instance = MagicMock()
        mock_state_graph.return_value = mock_state_graph_instance
        mock_chat_instance = MagicMock()
        mock_chat_openai.return_value = mock_chat_instance

        # Create agent
        agent = ScholarAgent(self.api_key, tools=self.mock_tools)

        # Test with empty results from retrieve_articles
        state = {
            "messages": [
                MockHumanMessage("machine learning"),  # Original query
                MockHumanMessage("[]"),  # Empty results from retrieve_articles
            ]
        }
        new_state = agent.rerank_articles(state)

        # Verify empty results handling
        self.assertIn("messages", new_state)
        self.assertEqual(len(new_state["messages"]), 1)
        self.assertEqual(new_state["messages"][0].content, "[]")  # Should still return "[]"

        # Test with malformed message content
        state = {
            "messages": [
                MockHumanMessage("machine learning"),  # Original query
                MockHumanMessage("invalid results"),  # Invalid results that can't be evaluated
            ]
        }
        new_state = agent.rerank_articles(state)

        # Verify error handling for malformed content
        self.assertIn("messages", new_state)
        self.assertEqual(len(new_state["messages"]), 1)
        self.assertEqual(new_state["messages"][0].content, "[]")  # Should return "[]" on error

    @patch("agent.scholar_agent.print")
    def test_rerank_articles_exception(self, mock_print, mock_chat_openai, mock_state_graph):
        """Test rerank_articles method handling exceptions."""
        # Setup mocks
        mock_state_graph_instance = MagicMock()
        mock_state_graph.return_value = mock_state_graph_instance
        mock_chat_instance = MagicMock()
        mock_chat_openai.return_value = mock_chat_instance

        # Setup mock reranker that raises an exception
        mock_reranker = MagicMock()
        mock_reranker.name = "cohere_reranker"
        mock_reranker.rerank.side_effect = Exception("API error")

        # Create agent with the mock reranker
        agent = ScholarAgent(self.api_key, tools=[mock_reranker])
        agent.reranker = mock_reranker  # Directly set the reranker

        # Construct a realistic state with formatted results
        formatted_results = [
            {
                "author_profile": {"metadata": {"author": "Professor A"}},
                "website_content": [{"text": "Article about machine learning by Professor A"}],
                "journal_content": [],
            }
        ]

        # Create the input state
        state = {
            "messages": [
                MockHumanMessage("machine learning"),  # Original query
                MockHumanMessage(str(formatted_results)),  # Results from retrieve_articles
            ]
        }

        # Test rerank_articles with an exception
        new_state = agent.rerank_articles(state)

        # Verify exception handling
        self.assertIn("messages", new_state)
        self.assertEqual(len(new_state["messages"]), 1)

        # Reranker should still be called, but error is caught
        mock_reranker.rerank.assert_called_once()

        # Check that error was printed, but don't check for the exact message
        # because the implementation might format it differently
        mock_print_calls = [" ".join(map(str, call_args[0])) for call_args in mock_print.call_args_list]
        self.assertTrue(
            any(("Error" in call and "API error" in call) for call in mock_print_calls),
            "No API error message was printed",
        )


if __name__ == "__main__":
    unittest.main()
