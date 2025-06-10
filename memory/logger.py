import datetime
import sqlite3
import os
from utils.file_utils import read_file
from .database import initialize_database

DB_PATH = os.path.join(os.path.dirname(__file__), 'autocoder.db')

def generate_app():
    """Generate an application"""
    initialize_database()
    # ...existing code...

def log_memory(old_content, new_content):
    """Log code changes to memory"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('src/backend/memory/log.txt', 'a') as file:  # Updated file path
        file.write(f"{timestamp} - Change: {old_content[:50]}... -> {new_content[:50]}...\n")

def log_edit(file_path, new_content):
    """Log an edit to the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Find the most recent version of this file
    c.execute(
        "SELECT id, content FROM files WHERE file_path = ? ORDER BY created_at DESC LIMIT 1",
        (file_path,)
    )
    file_row = c.fetchone()
    
    if file_row:
        file_id, old_content = file_row
        if old_content != new_content:
            c.execute(
                "INSERT INTO edits (file_id, old_content, new_content, operation) VALUES (?, ?, ?, ?)",
                (file_id, old_content, new_content, "update")
            )
            conn.commit()
    
    conn.close()
def get_edit_history(file_path):
    """Get edit history for a specific file"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT e.old_content, e.new_content, e.timestamp 
        FROM edits e
        JOIN files f ON e.file_id = f.id
        WHERE f.file_path = ?
        ORDER BY e.timestamp DESC
    ''', (file_path,))
    
    history = []
    for row in c.fetchall():
        history.append({
            "old_content": row[0],
            "new_content": row[1],
            "timestamp": row[2]
        })
    
    conn.close()
    return history
def get_file_content(file_path):    
    """Get the content of a file"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT content FROM files WHERE file_path = ?", (file_path,))
    row = c.fetchone()
    
    if row:
        return row[0]
    else:
        return None
def get_all_files():
    """Get all files in the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT file_path, content FROM files")
    files = {row[0]: row[1] for row in c.fetchall()}
    
    conn.close()
    return files
def get_file_history(file_path):
    """Get the history of a specific file"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT e.old_content, e.new_content, e.timestamp 
        FROM edits e
        JOIN files f ON e.file_id = f.id
        WHERE f.file_path = ?
        ORDER BY e.timestamp DESC
    ''', (file_path,))
    
    history = []
    for row in c.fetchall():
        history.append({
            "old_content": row[0],
            "new_content": row[1],
            "timestamp": row[2]
        })
    
    conn.close()
    return history