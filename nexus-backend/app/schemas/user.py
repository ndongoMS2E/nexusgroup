from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: str = "ouvrier"
    chantier_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    role: str
    is_active: bool
    chantier_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
