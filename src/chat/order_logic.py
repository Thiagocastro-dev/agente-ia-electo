from repository.relational.order_repository import OrderRepository
from repository.relational.models import DBOrder
from typing import List, Dict, Any
import logging
import re
from decimal import Decimal

class OrderLogic:
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    def process_intent(self, order: DBOrder, intent: str, items: List[Dict[str, Any]], user_message: str, llm_response: str, context: str) -> str:
        """
        Direciona a lógica de negócio com base na intenção detectada pelo LLM.
        """
        if intent == "ADD_TO_ORDER":
            return self.handle_add_to_order(order, items, llm_response)
        
        elif intent == "REQUEST_ADDRESS":
            return self.handle_request_address(order, llm_response)
        
        elif intent == "PROVIDE_ADDRESS":
            return self.handle_provide_address(order, user_message, context, llm_response)
            
        elif intent == "CONFIRM_ORDER":
            return self.handle_confirm_order(order, llm_response)
        
        elif intent == "PAYMENT_CONFIRMED":
            return self.handle_payment_confirmed(order, llm_response)

        else: # INQUIRY, GREETING, FALLBACK, etc.
            return llm_response

    def handle_add_to_order(self, order: DBOrder, new_items: List[Dict[str, Any]], llm_response: str) -> str:
        if not new_items:
            return "Parece que você quer adicionar algo, mas não entendi o quê. 🤔 Pode me dizer qual doce e a quantidade?"

        current_items = order.items.copy() if order.items else []
        
        for new_item in new_items:
            if 'price' not in new_item or not isinstance(new_item['price'], (int, float)):
                logging.warning(f"LLM tentou adicionar item sem preço válido: {new_item}")
                continue

            found = False
            for existing_item in current_items:
                if existing_item.get("product_name") == new_item.get("product_name"):
                    existing_item["quantity"] = int(existing_item.get("quantity", 0)) + int(new_item.get("quantity", 1))
                    found = True
                    break
            if not found:
                current_items.append(new_item)
        
        self.order_repo.update_order(order.id, items=current_items)
        return llm_response

    def handle_request_address(self, order: DBOrder, llm_response: str) -> str:
        self.order_repo.update_order(order.id, status="awaiting_address")
        return llm_response

    def handle_provide_address(self, order: DBOrder, user_message: str, context: str, llm_response: str) -> str:
        """
        Calcula o frete baseado no endereço e no contexto, atualiza o pedido.
        """
        freight_cost = self._calculate_freight(user_message, context)
        
        self.order_repo.update_order(
            order.id,
            delivery_address=user_message,
            freight_cost=freight_cost
        )
        # Recarrega o pedido para obter o total atualizado
        updated_order = self.order_repo.get_order_by_id(order.id)
        
        # Anexa o valor do frete e o total à resposta do LLM
        final_response = (
            f"{llm_response}\n\n"
            f"Taxa de entrega: *R$ {freight_cost:.2f}*\n"
            f"Total do Pedido (com entrega): *R$ {updated_order.total_amount:.2f}*"
        ).replace('.', ',')
        
        return final_response
        
    def _calculate_freight(self, address: str, context: str) -> Decimal:
        """
        Usa uma heurística para extrair a taxa de frete do contexto com base no bairro.
        """
        logging.info(f"Calculando frete para o endereço: {address}")
        # Simplificação: procura por bairros mencionados no endereço e no contexto.
        # Uma abordagem mais robusta usaria o LLM para fazer esse match.
        address_lower = address.lower()
        
        try:
            # Tenta extrair bairros das regras de entrega no contexto
            delivery_rules = re.search(r"taxas de entrega aproximadas:.*", context, re.IGNORECASE | re.DOTALL)
            if delivery_rules:
                rules_text = delivery_rules.group(0)
                for line in rules_text.split('\n'):
                    line_lower = line.lower()
                    if 'bairro' in line_lower:
                        # Extrai o nome do bairro, ex: "Bairro de Nazaré" -> "nazaré"
                        match = re.search(r"bairro de ([\w\s]+):|bairros ([\w\s,]+):", line_lower)
                        if not match: continue

                        bairros = (match.group(1) or match.group(2)).strip().split(',')
                        bairros = [b.strip() for b in bairros]

                        if any(bairro in address_lower for bairro in bairros):
                            # Extrai o valor em R$ da linha
                            price_match = re.search(r"r\$\s*([\d,\.]+)", line_lower)
                            if price_match:
                                price_str = price_match.group(1).replace('.', '').replace(',', '.')
                                logging.info(f"Bairro correspondente encontrado: {bairros[0]}. Frete: R$ {price_str}")
                                return Decimal(price_str)
        except Exception as e:
            logging.error(f"Erro ao calcular frete com regex: {e}")

        logging.warning("Nenhum bairro correspondente encontrado. Usando frete padrão de consulta.")
        return Decimal("18.00") # Valor padrão "outras regiões sob consulta"


    def handle_confirm_order(self, order: DBOrder, llm_response: str) -> str:
        if not order.items:
             return "Seu carrinho está vazio! 🛒 Que tal escolher uma de nossas delícias primeiro? Temos bolos, macarons e muito mais! 🍰"
        
        self.order_repo.update_order(order.id, status="awaiting_payment")
        
        # Monta a resposta final com os detalhes do pagamento
        pix_key = "doce.vida@email.com (PIX EMAIL)"
        final_response = (
            f"{llm_response}\n\n"
            "Para confirmar, você pode fazer o pagamento via PIX para a chave abaixo:\n\n"
            f"🔑 **Chave Pix:** `{pix_key}`\n"
            f"💰 **Valor Total:** R$ {order.total_amount:.2f}\n\n"
            "É só me mandar um 'pago' ou 'confirmado' assim que fizer o pagamento, que eu já mando seu pedido para o preparo! 🥰"
        ).replace('.', ',')
        
        return final_response
        
    def handle_payment_confirmed(self, order: DBOrder, llm_response: str) -> str:
        """
        Finaliza o pedido, atualiza o status e "envia para a cozinha".
        """
        self.order_repo.update_order(order.id, status="confirmed")
        self._send_to_kitchen(order)
        
        return llm_response

    def _send_to_kitchen(self, order: DBOrder):
        """
        (Simulação) Envia os detalhes do pedido para a cozinha/sistema de gestão.
        """
        logging.info("🚀 ENVIANDO PEDIDO PARA A COZINHA 🚀")
        logging.info(f"  - ID do Pedido: {order.id}")
        logging.info(f"  - Session ID (Cliente): {order.session_id}")
        logging.info(f"  - Endereço de Entrega: {order.delivery_address}")
        logging.info(f"  - Valor Total: {order.total_amount}")
        logging.info("  - Itens:")
        for item in order.items:
            logging.info(f"    * {item['quantity']}x {item['product_name']} (R$ {item['price']})")
        logging.info("🚀 PEDIDO ENVIADO COM SUCESSO 🚀")
