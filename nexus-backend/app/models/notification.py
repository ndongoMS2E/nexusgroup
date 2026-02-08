from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from datetime import datetime
from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type_notif = Column(String(50), nullable=False)  # info, warning, danger, success
    categorie = Column(String(50), nullable=False)  # stock, depense, presence, chantier
    is_read = Column(Boolean, default=False)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
