from sqlalchemy.orm import sessionmaker
from .models import DBDocument
from .pg_db import engine
from datetime import datetime

Session = sessionmaker(bind=engine)

class DocumentRepository:
    def __init__(self):
        self.session = Session()

    def add_document(self, hash, filename, state, num_parts):
        doc = DBDocument(
            hash=hash,
            filename=filename,
            state=state,
            num_parts=num_parts,
            processed_parts=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.session.add(doc)
        self.session.commit()
        return doc

    def update_document_state(self, doc_id, state, processed_parts=None):
        doc = self.session.query(DBDocument).filter_by(id=doc_id).first()
        if doc:
            doc.state = state
            if processed_parts is not None:
                doc.processed_parts = processed_parts
            doc.updated_at = datetime.now()
            self.session.commit()
        return doc

    def get_document_by_hash(self, hash):
        return self.session.query(DBDocument).filter_by(hash=hash).first()

    def get_document_by_id(self, doc_id):
        return self.session.query(DBDocument).filter_by(id=doc_id).first()

    def list_documents_by_state(self, state):
        return self.session.query(DBDocument).filter_by(state=state).all()

    def list_all_documents(self):
        return self.session.query(DBDocument).all()
