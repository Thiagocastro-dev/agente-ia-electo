from sqlalchemy.orm import sessionmaker
from .models import DBDocumentPart
from .pg_db import engine
from datetime import datetime

Session = sessionmaker(bind=engine)

class DocumentPartRepository:
    def __init__(self):
        self.session = Session()

    def add_part(self, document_id, part_id, state):
        part = DBDocumentPart(
            document_id=document_id,
            part_id=part_id,
            state=state,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.session.add(part)
        self.session.commit()
        return part

    def update_part_state(self, document_id, part_id, state):
        part = self.session.query(DBDocumentPart).filter_by(document_id=document_id, part_id=part_id).first()
        if part:
            part.state = state
            part.updated_at = datetime.now()
            self.session.commit()
        return part

    def get_part(self, document_id, part_id):
        return self.session.query(DBDocumentPart).filter_by(document_id=document_id, part_id=part_id).first()

    def list_parts_by_document(self, document_id):
        return self.session.query(DBDocumentPart).filter_by(document_id=document_id).all()
