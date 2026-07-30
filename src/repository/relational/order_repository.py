from sqlalchemy.orm import sessionmaker
from .models import DBOrder
from .pg_db import engine
from typing import Optional, Dict, Any, List
from decimal import Decimal

Session = sessionmaker(bind=engine)

class OrderRepository:
    def __init__(self):
        self.session = Session()

    def get_or_create_active_order(self, session_id: str) -> DBOrder:
        """
        Recupera o pedido ativo (status 'draft' ou 'awaiting_address') 
        ou cria um novo se não houver nenhum.
        """
        active_statuses = ['draft', 'awaiting_address']
        order = self.session.query(DBOrder)\
            .filter(DBOrder.session_id == session_id, DBOrder.status.in_(active_statuses))\
            .first()

        if not order:
            order = DBOrder(session_id=session_id, status='draft', items=[])
            self.session.add(order)
            self.session.commit()
            
        return order

    def update_order(self, order_id: int, **kwargs: Any) -> DBOrder:
        """
        Atualiza um pedido com os dados fornecidos.
        Recalcula os totais se os itens ou o frete mudarem.
        """
        order = self.session.query(DBOrder).filter_by(id=order_id).one()
        
        recalculate = False
        for key, value in kwargs.items():
            if hasattr(order, key):
                setattr(order, key, value)
                if key in ['items', 'freight_cost']:
                    recalculate = True
        
        if recalculate:
            self.recalculate_totals(order)

        self.session.commit()
        return order
        
    def recalculate_totals(self, order: DBOrder):
        """
        Calcula o subtotal e o total com base nos itens e no custo do frete.
        """
        subtotal = sum(Decimal(item['price']) * int(item['quantity']) for item in order.items)
        order.subtotal = subtotal
        
        freight_cost = order.freight_cost or Decimal('0.00')
        order.total_amount = subtotal + freight_cost

    def get_order_by_id(self, order_id: int) -> Optional[DBOrder]:
        return self.session.query(DBOrder).filter_by(id=order_id).first()
