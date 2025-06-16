# models/__init__.py
"""
Database models and utilities for the Hostel Management System
"""

try:
    from .database import db, Database, StudentDB
    print("✅ Database models imported successfully")
except ImportError as e:
    print(f"⚠️  Error importing database models: {e}")
    # Create fallback objects
    db = None
    Database = None
    StudentDB = None

__all__ = ['db', 'Database', 'StudentDB']