#!/usr/bin/env python3
"""
Cleanup script for deleting old pastes automatically.
This script should be run periodically (e.g., via cron job or task scheduler).
"""
import sys
import os
from pathlib import Path

# Add the app directory to Python path
app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
sys.path.insert(0, app_dir)

from database import SessionLocal
import crud

def main():
    """Run the cleanup process"""
    print("Starting cleanup process...")
    
    db = SessionLocal()
    try:
        deleted_count = crud.delete_old_pastes(db, days=5)
        print(f"Cleanup completed: deleted {deleted_count} old pastes")
        return deleted_count
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    main()
