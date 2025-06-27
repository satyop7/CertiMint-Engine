"""
Database uploader for results
"""
import json
import sqlite3
import os

def upload_to_database(result_data):
    """Upload result to database"""
    # Create database if it doesn't exist
    db_path = "results.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignment_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id TEXT UNIQUE,
            username TEXT,
            subject TEXT,
            status TEXT,
            plagiarism_score REAL,
            relevance_score REAL,
            timestamp TEXT,
            full_result TEXT
        )
    ''')
    
    # Insert or update result
    cursor.execute('''
        INSERT OR REPLACE INTO assignment_results 
        (assignment_id, username, subject, status, plagiarism_score, relevance_score, timestamp, full_result)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        result_data.get('assignment_id'),
        result_data.get('username'),
        result_data.get('subject'),
        result_data.get('status'),
        result_data.get('plagiarism_check', {}).get('plagiarism_percentage', 0),
        result_data.get('content_validation', {}).get('relevance_score', 0),
        result_data.get('timestamp'),
        json.dumps(result_data)
    ))
    
    conn.commit()
    conn.close()
    
    print(f"Result uploaded to database: {result_data.get('assignment_id')}")

def clear_data_directory():
    """Clear all files from data directory except info.json"""
    data_dir = "data"
    
    if not os.path.exists(data_dir):
        return
    
    for filename in os.listdir(data_dir):
        if filename != "info.json":
            file_path = os.path.join(data_dir, filename)
            try:
                os.remove(file_path)
                print(f"Removed: {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")