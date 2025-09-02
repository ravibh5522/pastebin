#!/bin/bash
set -e

# Create necessary directories
mkdir -p data uploads logs

# Wait for database to be ready (if using external database)
if [[ "$DATABASE_URL" == postgresql* ]] || [[ "$DATABASE_URL" == mysql* ]]; then
    echo "Waiting for database to be ready..."
    python -c "
import time
import sys
from sqlalchemy import create_engine
import os

max_retries = 30
retry_interval = 2
db_url = os.getenv('DATABASE_URL')

for i in range(max_retries):
    try:
        engine = create_engine(db_url)
        engine.connect()
        print('Database is ready!')
        break
    except Exception as e:
        if i == max_retries - 1:
            print(f'Failed to connect to database after {max_retries} attempts')
            sys.exit(1)
        print(f'Database not ready (attempt {i+1}/{max_retries}): {e}')
        time.sleep(retry_interval)
"
fi

# Initialize database
python -c "from app.database import create_db_and_tables; create_db_and_tables(); print('Database initialized!')"

# Run cleanup once
python -c "
from app.database import SessionLocal
from app import crud
import os

db = SessionLocal()
try:
    days = int(os.getenv('AUTO_DELETE_DAYS', '5'))
    deleted = crud.delete_old_pastes(db, days=days)
    print(f'Initial cleanup: deleted {deleted} old pastes')
except Exception as e:
    print(f'Initial cleanup error: {e}')
finally:
    db.close()
"

echo "Starting Pastebin application..."

# Start the application
exec "$@"
