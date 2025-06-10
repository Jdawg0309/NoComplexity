import sqlite3
import os
import json
from datetime import datetime
import hashlib

DB_PATH = os.path.join(os.path.dirname(__file__), 'autocoder.db')

def initialize_database():
    """Initialize the database"""
    os.makedirs("memory", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Projects table
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT NOT NULL,
        hash TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Files table
    c.execute('''CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        file_path TEXT NOT NULL,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    )''')
    
    # Edits table
    c.execute('''CREATE TABLE IF NOT EXISTS edits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER,
        old_content TEXT,
        new_content TEXT,
        operation TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (file_id) REFERENCES files (id)
    )''')
    
    conn.commit()
    conn.close()

def save_project_snapshot(project_path, original_files, updated_files):
    """Save a snapshot of the project before and after changes"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create project hash
    project_hash = hash_project(project_path)
    
    # Insert or get project
    c.execute("SELECT id FROM projects WHERE hash=?", (project_hash,))
    project_row = c.fetchone()
    
    if project_row:
        project_id = project_row[0]
    else:
        c.execute(
            "INSERT INTO projects (path, hash) VALUES (?, ?)",
            (project_path, project_hash)
        )
        project_id = c.lastrowid
    
    # Process files
    for file_path, content in original_files.items():
        # Get file ID
        c.execute(
            "SELECT id FROM files WHERE project_id=? AND file_path=?",
            (project_id, file_path)
        )
        file_row = c.fetchone()
        
        if file_row:
            file_id = file_row[0]
            # Save old content as edit
            old_content = content
            new_content = updated_files.get(file_path, content)
            
            if old_content != new_content:
                c.execute(
                    "INSERT INTO edits (file_id, old_content, new_content, operation) VALUES (?, ?, ?, ?)",
                    (file_id, old_content, new_content, "update")
                )
        else:
            # Insert new file
            c.execute(
                "INSERT INTO files (project_id, file_path, content) VALUES (?, ?, ?)",
                (project_id, file_path, content)
            )
            file_id = c.lastrowid
    
    conn.commit()
    conn.close()
    return project_hash

def hash_project(project_path):
    """Create a unique hash for the project"""
    if os.path.isfile(project_path):
        return hashlib.md5(project_path.encode()).hexdigest()
    
    # For directories, hash the structure
    structure = []
    for root, dirs, files in os.walk(project_path):
        for file in files:
            path = os.path.join(root, file)
            structure.append(path)
    
    return hashlib.md5(json.dumps(sorted(structure)).encode()).hexdigest()

def get_project_history(project_hash):
    """Get edit history for a project"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT e.operation, e.timestamp, f.file_path 
        FROM edits e
        JOIN files f ON e.file_id = f.id
        JOIN projects p ON f.project_id = p.id
        WHERE p.hash = ?
        ORDER BY e.timestamp DESC
    ''', (project_hash,))
    
    history = []
    for row in c.fetchall():
        history.append({
            "operation": row[0],
            "timestamp": row[1],
            "file_path": row[2]
        })
    
    conn.close()
    return history