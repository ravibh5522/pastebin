from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime
import os

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/pastes.db")

# Create data directory if using SQLite
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    os.makedirs("data", exist_ok=True)

# Configure engine based on database type
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # For PostgreSQL, MySQL, etc.
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Association table for group members
group_members = Table(
    'group_members',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('joined_at', DateTime, default=datetime.datetime.utcnow),
    Column('is_admin', Boolean, default=False),
    Column('is_acting_leader', Boolean, default=False)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    pastes = relationship("Paste", back_populates="owner")
    saved_pastes = relationship("SavedPaste", back_populates="user")
    groups = relationship("Group", secondary=group_members, back_populates="members")
    messages = relationship("Message", back_populates="sender")
    created_groups = relationship("Group", back_populates="creator")

class Paste(Base):
    __tablename__ = "pastes"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)
    content = Column(Text, nullable=True)  # <-- CHANGED: Content can be empty
    filenames = Column(String, nullable=True) # <-- NEW: To store file names
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Optional for anonymous pastes
    
    # Relationships
    owner = relationship("User", back_populates="pastes")
    saved_by = relationship("SavedPaste", back_populates="paste")

class SavedPaste(Base):
    __tablename__ = "saved_pastes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    paste_id = Column(Integer, ForeignKey("pastes.id"))
    saved_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="saved_pastes")
    paste = relationship("Paste", back_populates="saved_by")

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    creator_id = Column(Integer, ForeignKey("users.id"))
    is_private = Column(Boolean, default=False)
    invite_code = Column(String, unique=True, nullable=True)
    invite_code_updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="created_groups")
    members = relationship("User", secondary=group_members, back_populates="groups")
    messages = relationship("Message", back_populates="group")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=True)
    message_type = Column(String, default="text")  # text, code, file, system
    code_language = Column(String, nullable=True)  # for code messages
    file_path = Column(String, nullable=True)  # for file messages
    file_name = Column(String, nullable=True)  # original filename
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    edited_at = Column(DateTime, nullable=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    reply_to_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    
    # Relationships
    sender = relationship("User", back_populates="messages")
    group = relationship("Group", back_populates="messages")
    reply_to = relationship("Message", remote_side=[id])

def create_db_and_tables():
    Base.metadata.create_all(bind=engine)