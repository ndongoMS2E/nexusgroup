from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text
from datetime import datetime
from app.core.database import Base

class Chantier(Base):
    __tablename__ = "chantiers"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(200), nullable=False)
    reference = Column(String(50), unique=True, nullable=False)
    adresse = Column(String(300), nullable=False)
    ville = Column(String(100), default="Dakar")
    client_nom = Column(String(200), nullable=False)
    client_telephone = Column(String(20), nullable=True)
    budget_prevu = Column(Float, default=0)
    budget_consomme = Column(Float, default=0)
    progression = Column(Integer, default=0)
    status = Column(String(50), default="planifie")
    date_debut = Column(Date, nullable=True)
    date_fin = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
