from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class ChantierCreate(BaseModel):
    nom: str
    adresse: str
    ville: str = "Dakar"
    client_nom: str
    client_telephone: Optional[str] = None
    budget_prevu: float = 0
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    description: Optional[str] = None

class ChantierResponse(BaseModel):
    id: int
    nom: str
    reference: str
    adresse: str
    ville: str
    client_nom: str
    budget_prevu: float
    budget_consomme: float
    progression: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
