from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MaterielCreate(BaseModel):
    nom: str
    categorie: str
    unite: str
    quantite: float = 0
    seuil_alerte: float = 10
    prix_unitaire: float = 0
    chantier_id: int

class MaterielResponse(BaseModel):
    id: int
    nom: str
    categorie: str
    unite: str
    quantite: float
    seuil_alerte: float
    prix_unitaire: float
    chantier_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class MouvementCreate(BaseModel):
    materiel_id: int
    type_mouvement: str
    quantite: float
    motif: Optional[str] = None

class MouvementResponse(BaseModel):
    id: int
    materiel_id: int
    type_mouvement: str
    quantite: float
    motif: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
