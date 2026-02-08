from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class DepenseCreate(BaseModel):
    libelle: str
    description: Optional[str] = None
    categorie: str
    montant: float
    date_depense: date
    fournisseur: Optional[str] = None
    chantier_id: int

class DepenseResponse(BaseModel):
    id: int
    reference: str
    libelle: str
    description: Optional[str]
    categorie: str
    montant: float
    date_depense: date
    fournisseur: Optional[str]
    status: str
    chantier_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
