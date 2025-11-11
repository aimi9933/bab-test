#!/usr/bin/env python3
import sys
import os

print("Python version:", sys.version)
print("Current directory:", os.getcwd())
print("Python path:", sys.path[:3])

try:
    import fastapi
    print("FastAPI version:", fastapi.__version__)
except ImportError as e:
    print("FastAPI import error:", e)

try:
    import sqlalchemy
    print("SQLAlchemy version:", sqlalchemy.__version__)
except ImportError as e:
    print("SQLAlchemy import error:", e)