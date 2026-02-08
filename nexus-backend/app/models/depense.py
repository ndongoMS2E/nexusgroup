from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Depense(Base):
    __tablename__ = "depenses"
    
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(50), unique=True, nullable=False)
    libelle = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    categorie = Column(String(50), nullable=False)  # materiel, main_oeuvre, transport, autres
    montant = Column(Float, nullable=False)
    date_depense = Column(Date, nullable=False)
    fournisseur = Column(String(200), nullable=True)
    status = Column(String(50), default="en_attente")  # en_attente, approuvee, rejetee, payee
    
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
