from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(String(50), default="ouvrier")  # admin, comptable, chef_chantier, conducteur, ouvrier
    is_active = Column(Boolean, default=True)
    
    # Pour chef_chantier: chantier assigné
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
