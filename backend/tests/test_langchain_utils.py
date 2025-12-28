import unittest
from unittest.mock import MagicMock, patch
from backend.llm.langchain_utils import get_llm, invoke_chain
from langchain_openai import ChatOpenAI

class TestLangChainUtils(unittest.TestCase):

    def test_get_llm_openai(self):
        llm = get_llm(provider='openai', api_key='test_key')
        self.assertIsInstance(llm, ChatOpenAI)
        self.assertEqual(llm.openai_api_key.get_secret_value(), 'test_key')
        self.assertEqual(llm.model_name, 'gpt-3.5-turbo')

    def test_get_llm_deepseek(self):
        llm = get_llm(provider='deepseek', api_key='test_key')
        self.assertIsInstance(llm, ChatOpenAI)
        self.assertEqual(llm.openai_api_base, 'https://api.deepseek.com')
        self.assertEqual(llm.model_name, 'deepseek-chat')

    def test_get_llm_custom(self):
        llm = get_llm(provider='custom', api_key='test_key', base_url='http://custom.url', model_name='custom-model')
        self.assertEqual(llm.openai_api_base, 'http://custom.url')
        self.assertEqual(llm.model_name, 'custom-model')
