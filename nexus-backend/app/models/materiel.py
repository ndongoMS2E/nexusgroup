from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base

class Materiel(Base):
    __tablename__ = "materiels"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(200), nullable=False)
    categorie = Column(String(100), nullable=False)  # ciment, fer, bois, peinture, plomberie, electricite
    unite = Column(String(50), nullable=False)  # kg, sac, m3, piece, litre
    quantite = Column(Float, default=0)
    seuil_alerte = Column(Float, default=10)
    prix_unitaire = Column(Float, default=0)
    
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MouvementStock(Base):
    __tablename__ = "mouvements_stock"
    
    id = Column(Integer, primary_key=True, index=True)
    materiel_id = Column(Integer, ForeignKey("materiels.id"), nullable=False)
    type_mouvement = Column(String(20), nullable=False)  # entree, sortie
    quantite = Column(Float, nullable=False)
    motif = Column(String(300), nullable=True)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
