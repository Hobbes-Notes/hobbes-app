from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: str  # Google user ID
    email: EmailStr
    name: str
    picture_url: Optional[str] = None
    created_at: str

class UserCreate(BaseModel):
    id: str  # Google user ID
    email: EmailStr
    name: str
    picture_url: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    picture_url: Optional[str] = None