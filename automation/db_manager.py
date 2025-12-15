import sqlite3
import datetime
import os

DB_NAME = 'bot_history.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Table for Tech (HN)
    c.execute('''
        CREATE TABLE IF NOT EXISTS tech_posts (
            id TEXT PRIMARY KEY,
            title TEXT,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def is_tech_posted(story_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT 1 FROM tech_posts WHERE id = ?", (str(story_id),))
    result = c.fetchone()
    conn.close()
    return result is not None

def log_tech_post(story_id, title):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO tech_posts (id, title) VALUES (?, ?)", (str(story_id), title))
    conn.commit()
    conn.close()
