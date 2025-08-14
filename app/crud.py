from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from passlib.context import CryptContext
from datetime import datetime, timedelta
from . import database as models, schemas
import shutil
from pathlib import Path

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User CRUD operations
def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Paste CRUD operations
def get_paste_by_slug(db: Session, slug: str):
    """Retrieve a paste from the database by its unique slug."""
    return db.query(models.Paste).filter(models.Paste.slug == slug).first()

def create_paste(db: Session, paste: schemas.PasteCreate):
    """Create a new paste record in the database."""
    # This now includes filenames and user_id
    db_paste = models.Paste(
        slug=paste.slug, 
        content=paste.content, 
        filenames=paste.filenames,
        user_id=paste.user_id
    )
    db.add(db_paste)
    db.commit()
    db.refresh(db_paste)
    return db_paste

def get_user_pastes(db: Session, user_id: int):
    """Get all pastes created by a user"""
    return db.query(models.Paste).filter(models.Paste.user_id == user_id).order_by(models.Paste.created_at.desc()).all()

# Saved Paste CRUD operations
def save_paste(db: Session, user_id: int, paste_id: int):
    """Save a paste for a user"""
    # Check if already saved
    existing = db.query(models.SavedPaste).filter(
        and_(models.SavedPaste.user_id == user_id, models.SavedPaste.paste_id == paste_id)
    ).first()
    
    if existing:
        return existing
    
    db_saved_paste = models.SavedPaste(user_id=user_id, paste_id=paste_id)
    db.add(db_saved_paste)
    db.commit()
    db.refresh(db_saved_paste)
    return db_saved_paste

def unsave_paste(db: Session, user_id: int, paste_id: int):
    """Remove a saved paste for a user"""
    saved_paste = db.query(models.SavedPaste).filter(
        and_(models.SavedPaste.user_id == user_id, models.SavedPaste.paste_id == paste_id)
    ).first()
    
    if saved_paste:
        db.delete(saved_paste)
        db.commit()
        return True
    return False

def get_user_saved_pastes(db: Session, user_id: int):
    """Get all pastes saved by a user"""
    return db.query(models.SavedPaste).filter(models.SavedPaste.user_id == user_id).order_by(models.SavedPaste.saved_at.desc()).all()

def is_paste_saved_by_user(db: Session, user_id: int, paste_id: int):
    """Check if a paste is saved by a user"""
    return db.query(models.SavedPaste).filter(
        and_(models.SavedPaste.user_id == user_id, models.SavedPaste.paste_id == paste_id)
    ).first() is not None

# Auto-delete functionality
def delete_old_pastes(db: Session, days: int = 5):
    """Delete pastes older than specified days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    old_pastes = db.query(models.Paste).filter(models.Paste.created_at < cutoff_date).all()
    
    uploads_dir = Path("uploads")
    deleted_count = 0
    
    for paste in old_pastes:
        # Delete associated files
        paste_upload_dir = uploads_dir / paste.slug
        if paste_upload_dir.exists():
            try:
                shutil.rmtree(paste_upload_dir)
            except Exception as e:
                print(f"Error deleting files for paste {paste.slug}: {e}")
        
        # Delete saved paste entries
        db.query(models.SavedPaste).filter(models.SavedPaste.paste_id == paste.id).delete()
        
        # Delete the paste
        db.delete(paste)
        deleted_count += 1
    
    db.commit()
    return deleted_count