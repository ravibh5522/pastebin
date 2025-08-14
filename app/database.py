from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
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

def create_db_and_tables():
    Base.metadata.create_all(bind=engine)