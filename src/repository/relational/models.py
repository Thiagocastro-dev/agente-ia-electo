from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, JSON, func

Base = declarative_base()

class DBDocument(Base):
    __tablename__ = 'document'
    id = Column(Integer, primary_key=True)
    hash = Column(String)
    filename = Column(String)
    state = Column(String)
    num_parts = Column(Integer)
    processed_parts = Column(Integer)
    created_at = Column(Date)
    updated_at = Column(Date)
    
    def __repr__(self):
        return "<DBDocument(hash='{}', filename='{}', state='{}', num_parts={}, processed_parts={}, created_at={}, updated_at={})>"\
                .format(self.hash, self.filename, self.state, self.num_parts, self.processed_parts, self.created_at, self.updated_at)


class DBDocumentPart(Base):
    __tablename__ = 'document_part'
    document_id = Column(Integer, primary_key=True)
    part_id = Column(Integer, primary_key=True)
    state = Column(String)
    created_at = Column(Date)
    updated_at = Column(Date)
    
    def __repr__(self):
        return "<DBDocumentPart(document_id='{}', part_id='{}', state='{}', created_at={}, updated_at={})>"\
                .format(self.document_id, self.part_id, self.state, self.created_at, self.updated_at)


class DBChatMessage(Base):
    __tablename__ = 'chat_message'
    id = Column(Integer, primary_key=True)
    session_id = Column(String, index=True)
    sender = Column(String) # 'user' or 'assistant'
    message = Column(String)
    created_at = Column(DateTime)
    
    def __repr__(self):
        return "<DBChatMessage(id={}, session_id='{}', sender='{}', message='{}', created_at={})>"\
                .format(self.id, self.session_id, self.sender, self.message[:30] + '...' if len(self.message) > 30 else self.message, self.created_at)

class DBOrder(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    session_id = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False, default='draft') # draft, awaiting_payment, confirmed, cancelled
    items = Column(JSON, nullable=False, default=[]) # Ex: [{"product_name": "Bolo X", "quantity": 1, "price": 20.00}]
    delivery_address = Column(String, nullable=True)
    freight_cost = Column(Numeric(10, 2), nullable=True, default=0.00)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0.00)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<DBOrder(id={self.id}, session_id='{self.session_id}', status='{self.status}', total_amount={self.total_amount})>"

        