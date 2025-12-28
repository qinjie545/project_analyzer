import unittest
from unittest.mock import MagicMock, patch
from backend.analysis.mcp_agent import chat_completion_openai_compatible, analyze_repo_with_llm

class TestMCPAgent(unittest.TestCase):

    @patch('backend.llm.langchain_utils.get_llm')
    def test_chat_completion_openai_compatible(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        response = chat_completion_openai_compatible(api_key="key", prompt="hello")
        
        self.assertEqual(response, "Test response")
        mock_get_llm.assert_called_once()
        mock_llm.invoke.assert_called_once()

    @patch('backend.analysis.mcp_agent.chat_completion_openai_compatible')
    def test_analyze_repo_with_llm(self, mock_chat):
        mock_chat.return_value = "Analysis result"
        
        repo = {
            "full_name": "test/repo",
            "stargazers_count": 100,
            "language": "Python",
            "description": "Test repo"
        }
        
        result = analyze_repo_with_llm(repo, api_key="key")
        
        self.assertEqual(result['summary'], "Analysis result")
        mock_chat.assert_called_once()
        
    def test_analyze_repo_no_api_key(self):
        repo = {
            "full_name": "test/repo",
            "stargazers_count": 100,
            "language": "Python",
            "description": "Test repo"
        }
        result = analyze_repo_with_llm(repo, api_key=None)
        self.assertIn("test/repo uses Python", result['summary'])
