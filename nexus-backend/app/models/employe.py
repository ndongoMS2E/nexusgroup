from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey
from datetime import datetime
from app.core.database import Base

class Employe(Base):
    __tablename__ = "employes"
    
    id = Column(Integer, primary_key=True, index=True)
    matricule = Column(String(50), unique=True, nullable=False)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    telephone = Column(String(20), nullable=True)
    poste = Column(String(100), nullable=False)  # macon, ferrailleur, electricien, plombier, manoeuvre, chef_equipe
    salaire_journalier = Column(Float, nullable=False)
    date_embauche = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Presence(Base):
    __tablename__ = "presences"
    
    id = Column(Integer, primary_key=True, index=True)
    employe_id = Column(Integer, ForeignKey("employes.id"), nullable=False)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=False)
    date = Column(Date, nullable=False)
    heures_travaillees = Column(Float, default=8)
    status = Column(String(20), default="present")  # present, absent, retard
    commentaire = Column(String(300), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
