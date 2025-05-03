import unittest
import os
import json
from pathlib import Path
from scholar_agent import ScholarAgent, ChromaDBTool, create_scholar_agent
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

class TestScholarAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment before running tests"""
        # Ensure we're in test mode
        os.environ['TEST_MODE'] = 'true'
        
        # Create the agent for testing
        cls.chroma_tool = ChromaDBTool(api_key=os.getenv("OPENAI_API_KEY"), n_results=10)
        cls.agent = create_scholar_agent(tools=[cls.chroma_tool])

    def test_agent_initialization(self):
        """Test if the agent is properly initialized"""
        self.assertIsInstance(self.agent, ScholarAgent)
        self.assertIsNotNone(self.agent.tools)
        self.assertIsNotNone(self.agent.model)
        self.assertIsNotNone(self.agent.reranker)

    def test_basic_query(self):
        """Test if the agent can handle a basic query"""
        query = "deep learning"
        messages = [
            SystemMessage(content="You are a helpful research assistant."),
            HumanMessage(content=query),
            # Convert dict to JSON string for AIMessage
            AIMessage(content=json.dumps({"results": []}))
        ]
        
        try:
            result = self.agent.graph.invoke({"messages": messages})
            self.assertIsNotNone(result)
            
            # The result should be a dictionary
            self.assertIsInstance(result, dict)
            
            # It should contain either messages or experts
            self.assertTrue(
                'messages' in result or 'experts' in result,
                "Result should contain either messages or experts"
            )
            
            if 'experts' in result:
                # If we have experts, verify the structure
                self.assertIsInstance(result['experts'], list)
                
        except Exception as e:
            self.fail(f"Query failed with unexpected error: {str(e)}")

    def test_empty_query(self):
        """Test handling of empty queries"""
        query = ""
        messages = [
            HumanMessage(content=query),
        ]
        
        result = self.agent.graph.invoke({"messages": messages})
        self.assertIsNotNone(result)
        
        # For empty queries, we expect an empty result
        if 'experts' in result:
            self.assertEqual(len(result['experts']), 0)
        elif 'results' in result:
            self.assertEqual(len(result['results']), 0)

if __name__ == '__main__':
    unittest.main() 