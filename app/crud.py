from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from passlib.context import CryptContext
from datetime import datetime, timedelta
from . import database as models, schemas
from . import encryption
import shutil
import random
import string
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
    # Handle encryption for private pastes
    content = paste.content
    pin_hash = None
    encryption_salt = paste.encryption_salt  # Use pre-generated salt if provided
    
    if paste.is_private and paste.pin:
        pin_hash = encryption.hash_pin(paste.pin)
        
        # Generate salt only if not provided
        if not encryption_salt:
            encryption_salt = encryption.generate_salt()
        
        if content:
            content = encryption.encrypt_content(content, paste.pin, encryption_salt)
    
    db_paste = models.Paste(
        slug=paste.slug, 
        content=content, 
        filenames=paste.filenames,
        user_id=paste.user_id,
        is_private=paste.is_private,
        pin_hash=pin_hash,
        encryption_salt=encryption_salt,
        expires_at=paste.expires_at
    )
    db.add(db_paste)
    db.commit()
    db.refresh(db_paste)
    return db_paste

def decrypt_paste_content(paste, pin: str) -> str:
    """Decrypt paste content with the provided PIN."""
    if not paste.is_private or not paste.content:
        return paste.content
    
    if not encryption.verify_pin(pin, paste.pin_hash):
        raise ValueError("Invalid PIN")
    
    return encryption.decrypt_content(paste.content, pin, paste.encryption_salt)

def verify_paste_pin(paste, pin: str) -> bool:
    """Verify if the provided PIN is correct for the paste."""
    if not paste.is_private:
        return True
    return encryption.verify_pin(pin, paste.pin_hash)

def get_user_pastes(db: Session, user_id: int):
    """Get all pastes created by a user"""
    return db.query(models.Paste).filter(models.Paste.user_id == user_id).order_by(models.Paste.created_at.desc()).all()

def search_user_pastes(db: Session, user_id: int, search_query: str):
    """Search through user's pastes by slug or content"""
    if not search_query.strip():
        return []
    
    search_term = f"%{search_query.strip()}%"
    return db.query(models.Paste).filter(
        and_(
            models.Paste.user_id == user_id,
            or_(
                models.Paste.slug.ilike(search_term),
                models.Paste.content.ilike(search_term)
            )
        )
    ).order_by(models.Paste.created_at.desc()).all()

def search_saved_pastes(db: Session, user_id: int, search_query: str):
    """Search through user's saved pastes by slug or content"""
    if not search_query.strip():
        return []
    
    search_term = f"%{search_query.strip()}%"
    return db.query(models.SavedPaste).join(models.Paste).filter(
        and_(
            models.SavedPaste.user_id == user_id,
            or_(
                models.Paste.slug.ilike(search_term),
                models.Paste.content.ilike(search_term)
            )
        )
    ).order_by(models.SavedPaste.saved_at.desc()).all()

def search_all_pastes(db: Session, search_query: str, limit: int = 50):
    """Search through all PUBLIC pastes by slug or content"""
    if not search_query.strip():
        return []
    
    search_term = f"%{search_query.strip()}%"
    return db.query(models.Paste).filter(
        and_(
            models.Paste.is_private == False,  # Only search public pastes
            or_(
                models.Paste.slug.ilike(search_term),
                models.Paste.content.ilike(search_term)
            )
        )
    ).order_by(models.Paste.created_at.desc()).limit(limit).all()

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
    """Delete pastes that have expired (expires_at) or are older than specified days (fallback)"""
    from sqlalchemy import or_
    
    current_time = datetime.utcnow()
    cutoff_date = current_time - timedelta(days=days)
    
    # Delete pastes that:
    # 1. Have expires_at set and have expired, OR
    # 2. Have no expires_at set and are older than cutoff_date (legacy behavior)
    old_pastes = db.query(models.Paste).filter(
        or_(
            models.Paste.expires_at < current_time,  # Expired pastes
            (models.Paste.expires_at.is_(None)) & (models.Paste.created_at < cutoff_date)  # Legacy: no expiry, old pastes
        )
    ).all()
    
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

# Group CRUD operations
def generate_invite_code():
    """Generate a unique invite code for a group"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def create_group(db: Session, group: schemas.GroupCreate, creator_id: int):
    """Create a new group"""
    invite_code = generate_invite_code() if group.is_private else None
    
    db_group = models.Group(
        name=group.name,
        description=group.description,
        is_private=group.is_private,
        creator_id=creator_id,
        invite_code=invite_code
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    # Add creator as admin member
    db.execute(
        models.group_members.insert().values(
            group_id=db_group.id,
            user_id=creator_id,
            is_admin=True
        )
    )
    db.commit()
    
    return db_group

def get_user_groups(db: Session, user_id: int):
    """Get all groups a user is member of"""
    return db.query(models.Group).join(models.group_members).filter(
        models.group_members.c.user_id == user_id
    ).order_by(models.Group.created_at.desc()).all()

def get_group_by_id(db: Session, group_id: int):
    """Get group by ID"""
    return db.query(models.Group).filter(models.Group.id == group_id).first()

def get_group_by_invite_code(db: Session, invite_code: str):
    """Get group by invite code"""
    return db.query(models.Group).filter(models.Group.invite_code == invite_code).first()

def join_group(db: Session, group_id: int, user_id: int):
    """Add user to group"""
    # Check if user is already a member
    existing = db.execute(
        models.group_members.select().where(
            and_(
                models.group_members.c.group_id == group_id,
                models.group_members.c.user_id == user_id
            )
        )
    ).first()
    
    if existing:
        return False
    
    db.execute(
        models.group_members.insert().values(
            group_id=group_id,
            user_id=user_id,
            is_admin=False
        )
    )
    db.commit()
    return True

def leave_group(db: Session, group_id: int, user_id: int):
    """Remove user from group"""
    db.execute(
        models.group_members.delete().where(
            and_(
                models.group_members.c.group_id == group_id,
                models.group_members.c.user_id == user_id
            )
        )
    )
    db.commit()
    return True

def is_group_member(db: Session, group_id: int, user_id: int):
    """Check if user is a member of the group"""
    result = db.execute(
        models.group_members.select().where(
            and_(
                models.group_members.c.group_id == group_id,
                models.group_members.c.user_id == user_id
            )
        )
    ).first()
    return result is not None

def is_group_admin(db: Session, group_id: int, user_id: int):
    """Check if user is an admin of the group"""
    result = db.execute(
        models.group_members.select().where(
            and_(
                models.group_members.c.group_id == group_id,
                models.group_members.c.user_id == user_id,
                models.group_members.c.is_admin == True
            )
        )
    ).first()
    return result is not None

def get_group_members(db: Session, group_id: int):
    """Get all members of a group with their roles"""
    return db.query(
        models.User.id,
        models.User.username,
        models.User.email,
        models.group_members.c.joined_at,
        models.group_members.c.is_admin,
        models.group_members.c.is_acting_leader
    ).join(models.group_members).filter(
        models.group_members.c.group_id == group_id
    ).all()

def is_acting_leader(db: Session, group_id: int, user_id: int):
    """Check if user is an acting leader of the group"""
    result = db.execute(
        models.group_members.select().where(
            and_(
                models.group_members.c.group_id == group_id,
                models.group_members.c.user_id == user_id,
                models.group_members.c.is_acting_leader == True
            )
        )
    ).first()
    return result is not None

def set_acting_leader(db: Session, group_id: int, user_id: int, is_acting_leader: bool):
    """Set or remove acting leader status for a user"""
    db.execute(
        models.group_members.update().where(
            and_(
                models.group_members.c.group_id == group_id,
                models.group_members.c.user_id == user_id
            )
        ).values(is_acting_leader=is_acting_leader)
    )
    db.commit()
    return True

def add_member_by_username(db: Session, group_id: int, username: str):
    """Add a member to the group by username"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    
    # Check if user is already a member
    if is_group_member(db, group_id, user.id):
        return False
    
    # Add user to group
    db.execute(
        models.group_members.insert().values(
            group_id=group_id,
            user_id=user.id,
            joined_at=datetime.utcnow(),
            is_admin=False,
            is_acting_leader=False
        )
    )
    db.commit()
    return user

def remove_member_from_group(db: Session, group_id: int, user_id: int):
    """Remove a member from the group"""
    db.execute(
        models.group_members.delete().where(
            and_(
                models.group_members.c.group_id == group_id,
                models.group_members.c.user_id == user_id
            )
        )
    )
    db.commit()
    return True

def refresh_group_invite_code(db: Session, group_id: int):
    """Generate a new invite code for the group"""
    import random
    import string
    
    # Generate new 8-character invite code
    new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Ensure uniqueness
    while get_group_by_invite_code(db, new_code):
        new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Update the group
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if group:
        group.invite_code = new_code
        group.invite_code_updated_at = datetime.utcnow()
        db.commit()
        db.refresh(group)
    
    return group

def get_groups_needing_code_refresh(db: Session):
    """Get groups whose invite codes need to be refreshed (older than 1 hour)"""
    from datetime import timedelta
    cutoff_time = datetime.utcnow() - timedelta(hours=1)
    
    return db.query(models.Group).filter(
        models.Group.invite_code_updated_at < cutoff_time
    ).all()

# Message CRUD operations
def create_message(db: Session, message: schemas.MessageCreate, sender_id: int):
    """Create a new message"""
    db_message = models.Message(
        content=message.content,
        message_type=message.message_type,
        code_language=message.code_language,
        sender_id=sender_id,
        group_id=message.group_id,
        reply_to_id=message.reply_to_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def create_file_message(db: Session, file_message: schemas.MessageFile, sender_id: int):
    """Create a file message"""
    db_message = models.Message(
        message_type="file",
        file_name=file_message.file_name,
        file_path=file_message.file_path,
        sender_id=sender_id,
        group_id=file_message.group_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_group_messages(db: Session, group_id: int, limit: int = 50, offset: int = 0):
    """Get messages for a group"""
    return db.query(models.Message).filter(
        models.Message.group_id == group_id
    ).order_by(desc(models.Message.created_at)).limit(limit).offset(offset).all()

def get_group_messages_paginated(db: Session, group_id: int, before_id: int = None, limit: int = 20):
    """Get messages for a group with cursor-based pagination"""
    query = db.query(models.Message).filter(
        models.Message.group_id == group_id
    )
    
    if before_id:
        query = query.filter(models.Message.id < before_id)
    
    return query.order_by(desc(models.Message.created_at)).limit(limit).all()

def get_message_by_id(db: Session, message_id: int):
    """Get message by ID"""
    return db.query(models.Message).filter(models.Message.id == message_id).first()

def update_message(db: Session, message_id: int, content: str):
    """Update message content"""
    message = get_message_by_id(db, message_id)
    if message:
        message.content = content
        message.edited_at = datetime.utcnow()
        db.commit()
        db.refresh(message)
    return message

def delete_message(db: Session, message_id: int):
    """Delete a message"""
    message = get_message_by_id(db, message_id)
    if message:
        db.delete(message)
        db.commit()
        return True
    return False

def search_group_messages(db: Session, group_id: int, search_query: str, limit: int = 50):
    """Search messages within a group"""
    if not search_query.strip():
        return []
    
    search_term = f"%{search_query.strip()}%"
    return db.query(models.Message).filter(
        and_(
            models.Message.group_id == group_id,
            models.Message.content.ilike(search_term)
        )
    ).order_by(desc(models.Message.created_at)).limit(limit).all()

# ==================== Activity Logging ====================

import json

def log_activity(
    db: Session,
    action: str,
    user_id: int = None,
    ip_address: str = None,
    user_agent: str = None,
    resource_type: str = None,
    resource_id: str = None,
    extra_data: dict = None
):
    """Log an activity for analytics (no sensitive data)"""
    # Anonymize IP address (keep only first 3 octets for IPv4)
    anonymized_ip = None
    if ip_address:
        parts = ip_address.split('.')
        if len(parts) == 4:
            anonymized_ip = f"{parts[0]}.{parts[1]}.{parts[2]}.0"
        else:
            anonymized_ip = ip_address.split(':')[0] if ':' in ip_address else ip_address
    
    # Truncate user agent to reasonable length
    truncated_ua = user_agent[:255] if user_agent else None
    
    # Convert extra_data to JSON string
    extra_data_str = json.dumps(extra_data) if extra_data else None
    
    activity = models.ActivityLog(
        action=action,
        user_id=user_id,
        ip_address=anonymized_ip,
        user_agent=truncated_ua,
        resource_type=resource_type,
        resource_id=resource_id,
        extra_data=extra_data_str
    )
    db.add(activity)
    db.commit()
    return activity

def get_activity_stats(db: Session, days: int = 30):
    """Get activity statistics for analytics"""
    from sqlalchemy import func
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Total activities
    total_activities = db.query(func.count(models.ActivityLog.id)).filter(
        models.ActivityLog.created_at >= cutoff_date
    ).scalar()
    
    # Activities by action type
    activities_by_action = db.query(
        models.ActivityLog.action,
        func.count(models.ActivityLog.id).label('count')
    ).filter(
        models.ActivityLog.created_at >= cutoff_date
    ).group_by(models.ActivityLog.action).all()
    
    # Daily activity counts
    daily_activities = db.query(
        func.date(models.ActivityLog.created_at).label('date'),
        func.count(models.ActivityLog.id).label('count')
    ).filter(
        models.ActivityLog.created_at >= cutoff_date
    ).group_by(func.date(models.ActivityLog.created_at)).order_by('date').all()
    
    # Unique users (by IP for anonymous)
    unique_users = db.query(func.count(func.distinct(models.ActivityLog.user_id))).filter(
        models.ActivityLog.created_at >= cutoff_date,
        models.ActivityLog.user_id.isnot(None)
    ).scalar()
    
    return {
        'total_activities': total_activities,
        'activities_by_action': {action: count for action, count in activities_by_action},
        'daily_activities': [{'date': str(d), 'count': c} for d, c in daily_activities],
        'unique_users': unique_users
    }

def get_hourly_stats(db: Session, hours: int = 24):
    """Get hourly activity statistics"""
    from sqlalchemy import func, extract
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    hourly_activities = db.query(
        extract('hour', models.ActivityLog.created_at).label('hour'),
        func.count(models.ActivityLog.id).label('count')
    ).filter(
        models.ActivityLog.created_at >= cutoff_time
    ).group_by(extract('hour', models.ActivityLog.created_at)).all()
    
    return [{'hour': int(h), 'count': c} for h, c in hourly_activities]

def get_recent_activities(db: Session, limit: int = 50):
    """Get recent activities"""
    return db.query(models.ActivityLog).order_by(
        desc(models.ActivityLog.created_at)
    ).limit(limit).all()

def get_user_activity_count(db: Session, user_id: int):
    """Get activity count for a specific user"""
    from sqlalchemy import func
    
    return db.query(func.count(models.ActivityLog.id)).filter(
        models.ActivityLog.user_id == user_id
    ).scalar()

# ==================== Admin Functions ====================

def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    """Get all users with pagination"""
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user_by_id(db: Session, user_id: int):
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def update_user(db: Session, user_id: int, username: str = None, email: str = None, 
                is_active: bool = None, is_admin: bool = None):
    """Update user details"""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    if username is not None:
        user.username = username
    if email is not None:
        user.email = email
    if is_active is not None:
        user.is_active = is_active
    if is_admin is not None:
        user.is_admin = is_admin
    
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    """Delete a user and all their data"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    # Delete user's pastes
    pastes = db.query(models.Paste).filter(models.Paste.user_id == user_id).all()
    for paste in pastes:
        paste_upload_dir = Path("uploads") / paste.slug
        if paste_upload_dir.exists():
            try:
                shutil.rmtree(paste_upload_dir)
            except Exception:
                pass
        db.delete(paste)
    
    # Delete saved pastes
    db.query(models.SavedPaste).filter(models.SavedPaste.user_id == user_id).delete()
    
    # Delete user's messages
    db.query(models.Message).filter(models.Message.sender_id == user_id).delete()
    
    # Delete user
    db.delete(user)
    db.commit()
    return True

def reset_user_password(db: Session, user_id: int, new_password: str):
    """Reset user password"""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user

def get_total_users_count(db: Session):
    """Get total number of users"""
    from sqlalchemy import func
    return db.query(func.count(models.User.id)).scalar()

def get_total_pastes_count(db: Session):
    """Get total number of pastes"""
    from sqlalchemy import func
    return db.query(func.count(models.Paste.id)).scalar()

def get_total_groups_count(db: Session):
    """Get total number of groups"""
    from sqlalchemy import func
    return db.query(func.count(models.Group.id)).scalar()

def create_admin_user(db: Session, username: str, email: str, password: str):
    """Create an admin user if it doesn't exist"""
    existing = get_user_by_username(db, username)
    if existing:
        # Update to admin if exists
        existing.is_admin = True
        db.commit()
        return existing
    
    hashed_password = get_password_hash(password)
    db_user = models.User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_admin=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user