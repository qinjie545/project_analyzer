import unittest
from unittest.mock import MagicMock, patch
from backend.api_server import app

class TestLLMEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch('backend.llm.langchain_utils.get_llm')
    def test_model_config_test(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test Reply"
        mock_llm.invoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm

        payload = {
            'provider': 'openai',
            'apiKey': 'test_key',
            'baseUrl': 'http://test.url',
            'modelName': 'test-model'
        }
        
        response = self.client.post('/api/config/model/test', json=payload)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['reply'], "Test Reply")
        
        mock_get_llm.assert_called_with('openai', 'test_key', 'http://test.url', 'test-model')
        mock_llm.invoke.assert_called_once()
