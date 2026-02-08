from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from datetime import datetime
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    type_document = Column(String(50), nullable=False)  # photo, plan, facture, contrat, rapport
    fichier_path = Column(String(500), nullable=False)
    taille = Column(Integer, default=0)  # en bytes
    description = Column(Text, nullable=True)
    
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
