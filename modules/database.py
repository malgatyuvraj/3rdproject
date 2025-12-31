"""
Database Module for eFile Sathi
Handles SQLite connection and schema initialization
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Database path
DB_PATH = Path('data/digifest.db')

def get_db_connection():
    """Get database connection"""
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schema"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Enable foreign keys
    c.execute("PRAGMA foreign_keys = ON")
    
    # 1. Grievance Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS grievances (
        id TEXT PRIMARY KEY,
        subject TEXT NOT NULL,
        details TEXT,
        priority TEXT DEFAULT 'normal',
        status TEXT DEFAULT 'pending',
        submitted_date TEXT,
        due_date TEXT,
        resolved_date TEXT,
        department TEXT,
        citizen_name TEXT,
        contact TEXT,
        source_doc_id TEXT,
        updates_json TEXT  -- JSON list of updates
    )
    """)
    
    # 2. Workflows Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS workflows (
        doc_id TEXT PRIMARY KEY,
        title TEXT,
        current_status TEXT,
        created_at TEXT,
        updated_at TEXT,
        priority TEXT,
        expected_completion TEXT
    )
    """)
    
    # 3. Workflow Steps Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS workflow_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id TEXT NOT NULL,
        status TEXT NOT NULL,
        timestamp TEXT,
        officer TEXT,
        remarks TEXT,
        FOREIGN KEY (doc_id) REFERENCES workflows (doc_id) ON DELETE CASCADE
    )
    """)
    
    # 4. Documents Table (for metadata)
    c.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        filename TEXT,
        file_path TEXT,
        upload_date TEXT,
        file_type TEXT,
        file_size INTEGER,
        ocr_text TEXT,
        summary_json TEXT,  -- JSON dict of summaries
        metadata_json TEXT  -- JSON dict of compliance/entities
    )
    """)
    
    conn.commit()
    conn.close()
    print("✓ Database initialized successfully")

# Helper functions for JSON serialization
def adapt_json(data):
    return json.dumps(data)

def convert_json(blob):
    return json.loads(blob)

# Register adapters if needed (sqlite3 handles text naturally, but specific types might need help)
# For now, we manually handle JSON dumps/loads in the repository classes.
