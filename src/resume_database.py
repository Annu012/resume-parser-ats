"""SQLite Database for Resumes"""

import sqlite3
import json
from pathlib import Path

class ResumeDatabase:
    def __init__(self, db_path: str = "data/resumes.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS parsed_resumes (
            id INTEGER PRIMARY KEY,
            filename TEXT,
            name TEXT,
            email TEXT,
            parsed_data JSON,
            ats_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS job_matches (
            id INTEGER PRIMARY KEY,
            resume_id INTEGER,
            job_title TEXT,
            match_score REAL,
            FOREIGN KEY(resume_id) REFERENCES parsed_resumes(id)
        )''')
        
        conn.commit()
        conn.close()
    
    def save_resume(self, filename: str, name: str, email: str, parsed_data: dict, ats_score: float) -> int:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('INSERT INTO parsed_resumes (filename, name, email, parsed_data, ats_score) VALUES (?, ?, ?, ?, ?)',
                  (filename, name, email, json.dumps(parsed_data), ats_score))
        resume_id = c.lastrowid
        conn.commit()
        conn.close()
        return resume_id
    
    def get_statistics(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM parsed_resumes")
        count = c.fetchone()[0]
        c.execute("SELECT AVG(ats_score) FROM parsed_resumes WHERE ats_score > 0")
        avg_score = c.fetchone()[0] or 0
        conn.close()
        return {"total_resumes": count, "average_ats_score": round(avg_score, 2)}

# Test
if __name__ == "__main__":
    db = ResumeDatabase()
    resume_id = db.save_resume("test.pdf", "John", "john@email.com", {"skills": ["Python"]}, 85.5)
    stats = db.get_statistics()
    print(f"✅ DB working: {stats}")