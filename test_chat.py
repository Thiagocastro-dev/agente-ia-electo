import sys
import os

# 1. Add src to system path at the absolute top of the file
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 2. Set up environment variables required by settings BEFORE any module is imported or patched
os.environ["DOCINT_TCE_ENDPOINT"] = "http://mock-docint"
os.environ["DOCINT_TCE_APY_KEY"] = "mock-key"
os.environ["QDRANT_URL"] = "http://mock-qdrant:6333"
os.environ["QDRANT_COLLECTION"] = "mock-collection"
os.environ["AZOPENAI_API_KEY"] = "mock-key"
os.environ["AZOPENAI_API_ENDPOINT"] = "http://mock-azure"
os.environ["AZOPENAI_API_VERSION"] = "2024-02-15-preview"
os.environ["AZOPENAI_EMBEDDING_MODEL"] = "mock-emb"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5432"
os.environ["POSTGRES_USER"] = "postgres"
os.environ["POSTGRES_PASS"] = "postgres"
os.environ["POSTGRES_DATABASE"] = "rag_db"
os.environ["POSTGRES_SCHEMA"] = "rag"
os.environ["OCR_ENGINE"] = "Docling"
os.environ["GEMINI_API_KEY"] = "mock-gemini-key"

import unittest
from unittest.mock import MagicMock, patch

# Pre-import chat.chat_service to ensure it's registered in sys.modules
import chat.chat_service

class TestChatService(unittest.TestCase):

    @patch('chat.chat_service.ChatRepository')
    @patch('chat.chat_service.QdrantRepository')
    @patch('chat.chat_service.OrderRepository')
    @patch('chat.chat_service.genai.Client')
    def test_generate_response_flow(self, mock_genai_client, mock_order_repo, mock_qdrant_repo, mock_chat_repo):
        # Mock the Qdrant Repository similarity search
        mock_doc = MagicMock()
        mock_doc.page_content = "Bolo de Cenoura com calda de brigadeiro belga cremosa - R$ 15,00"
        mock_qdrant_repo.return_value.similarity_search.return_value = [mock_doc]

        # Mock Chat History
        mock_msg_1 = MagicMock()
        mock_msg_1.sender = "user"
        mock_msg_1.message = "Olá!"
        mock_msg_2 = MagicMock()
        mock_msg_2.sender = "assistant"
        mock_msg_2.message = "Olá! Como posso adoçar seu dia hoje? 🍰"
        mock_chat_repo.return_value.get_chat_history.return_value = [mock_msg_1, mock_msg_2]

        # Mock Gemini Response
        mock_gemini_response = MagicMock()
        mock_gemini_response.text = (
            '{"intent": "INQUIRY", "items": [], '
            '"response_to_user": "Temos o delicioso Bolo de Cenoura com calda de chocolate '
            'por apenas R$ 15,00! 🥕🍰"}'
        )
        mock_genai_client.return_value.models.generate_content.return_value = mock_gemini_response

        mock_order = MagicMock()
        mock_order.status = "draft"
        mock_order.items = []
        mock_order.total_amount = 0
        mock_order_repo.return_value.get_or_create_active_order.return_value = mock_order

        # Instantiate ChatService
        from chat.chat_service import ChatService
        service = ChatService()

        # Run generate_response
        import asyncio
        response_text = asyncio.run(service.generate_response("session-123", "Quais bolos vocês têm?"))

        # Assertions
        self.assertEqual(response_text, "Temos o delicioso Bolo de Cenoura com calda de chocolate por apenas R$ 15,00! 🥕🍰")
        
        # Verify database calls
        service.chat_repo.get_chat_history.assert_called_once_with("session-123", limit=10)
        service.qdrant_repo.similarity_search.assert_called_once_with("Quais bolos vocês têm?", k=5)
        
        # Verify saving of user & model messages
        self.assertEqual(service.chat_repo.add_message.call_count, 2)
        service.chat_repo.add_message.assert_any_call(session_id="session-123", sender="user", message="Quais bolos vocês têm?")
        service.chat_repo.add_message.assert_any_call(session_id="session-123", sender="assistant", message=response_text)

        # Verify Gemini Client generate_content call structure
        service.client.models.generate_content.assert_called_once()
        call_kwargs = service.client.models.generate_content.call_args[1]
        
        self.assertEqual(service.model_name, "gemini-1.5-flash")
        self.assertEqual(len(call_kwargs['contents']), 3) # History (2) + Current user msg (1)
        self.assertEqual(call_kwargs['contents'][0]['role'], 'user')
        self.assertEqual(call_kwargs['contents'][1]['role'], 'model')
        self.assertEqual(call_kwargs['contents'][2]['role'], 'user')
        
        # Assert system instruction contains retrieved context
        self.assertIn("Bolo de Cenoura", call_kwargs['config'].system_instruction)

if __name__ == '__main__':
    unittest.main()
