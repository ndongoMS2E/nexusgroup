from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

class EmployeCreate(BaseModel):
    nom: str
    prenom: str
    telephone: Optional[str] = None
    poste: str
    salaire_journalier: float
    date_embauche: date
    chantier_id: Optional[int] = None

class EmployeResponse(BaseModel):
    id: int
    matricule: str
    nom: str
    prenom: str
    telephone: Optional[str]
    poste: str
    salaire_journalier: float
    date_embauche: date
    is_active: bool
    chantier_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

class PresenceCreate(BaseModel):
    employe_id: int
    chantier_id: int
    date: str
    status: str = "present"
    heures: float = Field(default=8, alias="heures_travaillees")
    commentaire: Optional[str] = None
    
    class Config:
        populate_by_name = True

class PresenceResponse(BaseModel):
    id: int
    employe_id: int
    chantier_id: int
    date: date
    heures_travaillees: float
    status: str
    commentaire: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
