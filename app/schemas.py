from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

# Paste Schemas
class PasteBase(BaseModel):
    content: Optional[str] = None # <-- Make content optional
    filenames: Optional[str] = None # <-- Add optional filenames

class PasteCreate(PasteBase):
    slug: str
    user_id: Optional[int] = None  # Optional for anonymous pastes

class Paste(PasteBase):
    id: int
    slug: str
    created_at: datetime
    user_id: Optional[int] = None
    owner: Optional[User] = None

    class Config:
        from_attributes = True

# Saved Paste Schemas
class SavedPasteCreate(BaseModel):
    paste_id: int

class SavedPaste(BaseModel):
    id: int
    user_id: int
    paste_id: int
    saved_at: datetime
    paste: Paste
    
    class Config:
        from_attributes = True