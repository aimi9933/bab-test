#!/usr/bin/env python3
import sys
import os

print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("Current directory:", os.getcwd())

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
    print(f"Added to path: {backend_path}")

print("Python path:", sys.path[:3])

try:
    import fastapi
    print("FastAPI imported successfully")
except ImportError as e:
    print(f"FastAPI import failed: {e}")

try:
    from app.main import app
    print("Main app imported successfully")
    print(f"App title: {app.title}")
except Exception as e:
    print(f"Main app import failed: {e}")