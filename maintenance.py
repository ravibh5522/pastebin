#!/usr/bin/env python3
"""
Maintenance script for Pastebin application
Usage: python maintenance.py [command]
Commands: cleanup, stats, health
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal, create_db_and_tables
from app import crud
from app.database import User, Paste, SavedPaste
from sqlalchemy import func, text

def cleanup_old_pastes(days=None):
    """Remove pastes older than specified days"""
    if days is None:
        days = int(os.getenv('AUTO_DELETE_DAYS', '5'))
    
    db = SessionLocal()
    try:
        deleted = crud.delete_old_pastes(db, days=days)
        print(f"✅ Cleanup completed: {deleted} pastes deleted")
        return deleted
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return 0
    finally:
        db.close()

def show_statistics():
    """Display application statistics"""
    db = SessionLocal()
    try:
        # Count statistics
        total_pastes = db.query(func.count(Paste.id)).scalar() or 0
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_saved = db.query(func.count(SavedPaste.id)).scalar() or 0
        
        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(hours=24)
        recent_pastes = db.query(func.count(Paste.id)).filter(
            Paste.created_at >= yesterday
        ).scalar() or 0
        
        # Storage usage
        upload_dir = Path("uploads")
        if upload_dir.exists():
            total_size = sum(f.stat().st_size for f in upload_dir.rglob('*') if f.is_file())
            size_mb = total_size / (1024 * 1024)
        else:
            size_mb = 0
        
        print("📊 Pastebin Statistics")
        print("=" * 40)
        print(f"Total Pastes: {total_pastes}")
        print(f"Total Users: {total_users}")
        print(f"Saved Pastes: {total_saved}")
        print(f"Recent Activity (24h): {recent_pastes} new pastes")
        print(f"Storage Usage: {size_mb:.2f} MB")
        print(f"Auto-delete Days: {os.getenv('AUTO_DELETE_DAYS', '5')}")
        
    except Exception as e:
        print(f"❌ Statistics failed: {e}")
    finally:
        db.close()

def check_health():
    """Check application health"""
    try:
        # Test database connection
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ Database: Connected")
        
        # Check upload directory
        upload_dir = Path("uploads")
        if upload_dir.exists() and upload_dir.is_dir():
            print("✅ Uploads Directory: OK")
        else:
            print("⚠️  Uploads Directory: Missing")
            
        # Check data directory
        data_dir = Path("data")
        if data_dir.exists() and data_dir.is_dir():
            print("✅ Data Directory: OK")
        else:
            print("⚠️  Data Directory: Missing")
            
        # Check configuration
        if os.getenv('SECRET_KEY'):
            print("✅ Secret Key: Configured")
        else:
            print("❌ Secret Key: Missing")
            
        print("\n🏥 Health Check Complete")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python maintenance.py [command]")
        print("Commands:")
        print("  cleanup [days]  - Remove old pastes (default: 5 days)")
        print("  stats          - Show application statistics")
        print("  health         - Check application health")
        print("  init           - Initialize database")
        return
    
    command = sys.argv[1].lower()
    
    if command == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else None
        cleanup_old_pastes(days)
        
    elif command == "stats":
        show_statistics()
        
    elif command == "health":
        check_health()
        
    elif command == "init":
        try:
            create_db_and_tables()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
