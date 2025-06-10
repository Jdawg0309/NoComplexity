import datetime
import sqlite3
from .database import DB_PATH

def log_memory(old_content, new_content):
    """Log code changes to memory"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('memory/log.txt', 'a') as file:
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