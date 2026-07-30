from google import genai
from google.genai import types
import os
import json
import logging
from typing import List, Dict, Any
from decimal import Decimal

from repository.relational.chat_repository import ChatRepository
from repository.relational.order_repository import OrderRepository
from repository.vector.qdrant_repository import QdrantRepository
from .order_logic import OrderLogic

class ChatService:
    def __init__(self):
        self.chat_repo = ChatRepository()
        self.order_repo = OrderRepository()
        self.qdrant_repo = QdrantRepository()
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model_name = "gemini-1.5-flash"
        self.order_logic = OrderLogic(self.order_repo)

    def get_system_instruction(self, context_text: str, order_state: Dict[str, Any]) -> str:
        order_state_str = json.dumps(order_state, ensure_ascii=False, indent=2)
        
        return f"""Você é a Mel, uma assistente de vendas virtual para a "Doceria Doce Vida". Sua função é ser uma vendedora proativa, simpática e eficiente. 
Você deve guiar o cliente pelo funil de vendas, desde a descoberta de produtos até a confirmação do pedido, retornando SEMPRE um JSON estruturado.

---
FUNIL DE VENDAS E INTENÇÕES (Siga esta lógica):
1.  **INQUIRY/GREETING**: O cliente está explorando ou cumprimentando. Responda de forma calorosa e informativa, usando o CONTEXTO abaixo.
2.  **ADD_TO_ORDER**: O cliente expressa desejo por um ou mais produtos (ex: "quero um bolo", "adicione dois macarons"). Identifique os itens, extraia NOME, QUANTIDADE e PREÇO do CONTEXTO, e coloque-os na lista de 'items'.
3.  **REQUEST_ADDRESS**: Após adicionar itens, o fluxo natural é perguntar sobre entrega. Se o cliente concordar, use esta intenção.
4.  **PROVIDE_ADDRESS**: O cliente informa seu endereço/CEP. Apenas marque a intenção. O sistema irá calcular o frete.
5.  **CONFIRM_ORDER**: O cliente está satisfeito com os itens e o endereço e quer finalizar (ex: "é isso mesmo", "pode fechar", "quero pagar").
6.  **PAYMENT_CONFIRMED**: O cliente informa que já pagou (ex: "pago", "já fiz o pix", "confirmado").
7.  **FALLBACK**: Use esta intenção se não conseguir entender o pedido do cliente.

---
REGRAS E BOAS PRÁTICAS:
*   **Proatividade**: Se o carrinho estiver vazio, sugira produtos do CONTEXTO. Se já tiver itens, pergunte se deseja adicionar mais algo ou se "podemos seguir para a entrega?".
*   **Extração de Preços**: Ao adicionar um item, o campo 'price' no JSON DEVE ser extraído NUMERICAMENTE do CONTEXTO. Nunca o invente.
*   **Tom de Voz**: Mantenha a personalidade doce e amigável da Mel (com emojis 🍰✨) no campo "response_to_user".
*   **Consistência**: Sempre baseie suas respostas e os dados dos itens no CONTEXTO e no ESTADO DO PEDIDO ATUAL.

---
CONTEXTO (CARDÁPIO, REGRAS DE ENTREGA, HORÁRIOS):
{context_text}

---
ESTADO DO PEDIDO ATUAL DO CLIENTE:
{order_state_str}

---
Com base na última mensagem do cliente, analise o contexto, o estado do pedido, determine a próxima intenção no funil de vendas e gere a resposta.
Responda ESTRITAMENTE com um objeto JSON válido, sem nenhum texto ou formatação adicional.

Formato do JSON de Resposta:
{{
  "intent": "INTENCAO_DETECTADA",
  "items": [
    {{
      "product_name": "Nome do Produto Extraído do Contexto",
      "quantity": 1,
      "price": 22.00
    }}
  ],
  "response_to_user": "Resposta amigável e contextualizada para o cliente."
}}
"""

    async def generate_response(self, session_id: str, user_message: str) -> str:
        # 1. Obter estado atual do pedido e histórico
        order = self.order_repo.get_or_create_active_order(session_id)
        order_state = {
            "status": order.status,
            "items": order.items,
            "total_amount": float(order.total_amount)
        }
        history = self.chat_repo.get_chat_history(session_id, limit=10)
        
        # 2. Buscar contexto no Qdrant (Cardápio/Regras)
        context_docs = self.qdrant_repo.similarity_search(user_message, k=5)
        context_text = "\n\n".join([doc.page_content for doc in context_docs]) if context_docs else "Nenhuma informação do cardápio encontrada."

        # 3. Construir histórico para o Gemini
        contents = [{'role': 'user' if msg.sender == 'user' else 'model', 'parts': [{'text': msg.message}]} for msg in history]
        contents.append({'role': 'user', 'parts': [{'text': user_message}]})

        # 4. Chamar a API Gemini para obter intenção e resposta
        system_instruction = self.get_system_instruction(context_text, order_state)
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
                response_mime_type="application/json"
            )
        )

        # 5. Processar a resposta estruturada do Gemini
        try:
            llm_output = json.loads(response.text)
            intent = llm_output.get("intent", "UNKNOWN")
            items = llm_output.get("items", [])
            response_to_user = llm_output.get("response_to_user", "Desculpe, não entendi. Pode repetir?")

            # 6. Executar a lógica de negócio baseada na intenção
            final_response = self.order_logic.process_intent(
                order=order,
                intent=intent,
                items=items,
                user_message=user_message,
                llm_response=response_to_user,
                context=context_text
            )

        except (json.JSONDecodeError, AttributeError) as e:
            logging.error(f"Erro ao decodificar ou processar a resposta do LLM: {e}\nResposta recebida: {response.text}")
            final_response = "Ops, tivemos um probleminha para processar sua mensagem. 😥 Poderia tentar de novo, por favor?"

        # 7. Salvar conversa no histórico e retornar
        self.chat_repo.add_message(session_id=session_id, sender="user", message=user_message)
        self.chat_repo.add_message(session_id=session_id, sender="assistant", message=final_response)

        return final_response
