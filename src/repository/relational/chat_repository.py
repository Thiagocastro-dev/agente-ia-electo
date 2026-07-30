from sqlalchemy.orm import sessionmaker
from .models import DBChatMessage
from .pg_db import engine
from datetime import datetime
from typing import List

Session = sessionmaker(bind=engine)

class ChatRepository:
    def __init__(self):
        self.session = Session()

    def add_message(self, session_id: str, sender: str, message: str) -> DBChatMessage:
        chat_msg = DBChatMessage(
            session_id=session_id,
            sender=sender,
            message=message,
            created_at=datetime.utcnow()
        )
        self.session.add(chat_msg)
        self.session.commit()
        return chat_msg

    def get_chat_history(self, session_id: str, limit: int = 50) -> List[DBChatMessage]:
        """
        Retrieves the chat history for a session ordered chronologically.
        """
        return self.session.query(DBChatMessage)\
            .filter_by(session_id=session_id)\
            .order_by(DBChatMessage.created_at.asc())\
            .limit(limit)\
            .all()

    def clear_chat_history(self, session_id: str):
        """
        Deletes the chat history for a session.
        """
        self.session.query(DBChatMessage).filter_by(session_id=session_id).delete()
        self.session.commit()
