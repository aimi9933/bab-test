#!/bin/bash
set -e

echo "Starting LLM Provider Backend..."

# Create necessary directories
mkdir -p /app/backend/data
mkdir -p /app/backend/logs

# Run database initialization
echo "Initializing database..."
cd /app && python -c "from backend.app.db.init_db import init_db; init_db()"

# Try to restore from backup if it exists
if [ -f "/app/backend/data/config_backup.json" ]; then
  echo "Found backup file, restoring configuration..."
  cd /app && python -c "
from backend.app.core.config import get_settings
from backend.app.db.session import SessionLocal
from backend.app.services.backup import restore_from_backup
try:
    db = SessionLocal()
    result = restore_from_backup(db)
    db.close()
    print(f'Restored: {result}')
except Exception as e:
    print(f'Could not restore from backup: {e}')
" || true
fi

echo "Database ready. Starting Uvicorn..."

# Start the application
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 "$@"
