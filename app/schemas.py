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

# Group Schemas
class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: bool = False

class GroupCreate(GroupBase):
    pass

class Group(GroupBase):
    id: int
    created_at: datetime
    creator_id: int
    invite_code: Optional[str] = None
    creator: Optional[User] = None
    
    class Config:
        from_attributes = True

class GroupWithMembers(Group):
    members: List[User] = []

# Message Schemas
class MessageBase(BaseModel):
    content: Optional[str] = None
    message_type: str = "text"
    code_language: Optional[str] = None
    reply_to_id: Optional[int] = None

class MessageCreate(MessageBase):
    group_id: int

class MessageFile(BaseModel):
    file_name: str
    file_path: str
    group_id: int

class Message(MessageBase):
    id: int
    created_at: datetime
    edited_at: Optional[datetime] = None
    sender_id: int
    group_id: int
    file_name: Optional[str] = None
    sender: Optional[User] = None
    reply_to: Optional["Message"] = None
    
    class Config:
        from_attributes = True

# WebSocket message schemas
class WSMessage(BaseModel):
    type: str  # "message", "join", "leave", "typing", "error"
    data: dict