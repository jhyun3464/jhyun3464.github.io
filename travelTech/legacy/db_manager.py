import sqlite3
import datetime

DB_NAME = 'hn_data.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY,
            title TEXT,
            korean_title TEXT,
            url TEXT,
            summary_md TEXT,
            grade TEXT,
            slug TEXT,
            tags TEXT,
            is_published BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_article(article_data):
    """
    Saves an article to the database. Uses UPSERT logic based on ID.
    article_data: dict containing id, title, korean_title, url, summary_md, grade, slug, tags
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Check if exists
    c.execute("SELECT id FROM articles WHERE id = ?", (article_data['id'],))
    exists = c.fetchone()

    if exists:
        c.execute('''
            UPDATE articles SET
                title = ?,
                korean_title = ?,
                url = ?,
                summary_md = ?,
                grade = ?,
                slug = ?,
                tags = ?
            WHERE id = ?
        ''', (
            article_data['title'],
            article_data['korean_title'],
            article_data['url'],
            article_data['summary_md'],
            article_data['grade'],
            article_data['slug'],
            article_data['tags'],
            article_data['id']
        ))
    else:
        c.execute('''
            INSERT INTO articles (id, title, korean_title, url, summary_md, grade, slug, tags, is_published)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (
            article_data['id'],
            article_data['title'],
            article_data['korean_title'],
            article_data['url'],
            article_data['summary_md'],
            article_data['grade'],
            article_data['slug'],
            article_data['tags']
        ))

    conn.commit()
    conn.close()

def get_articles():
    """
    Returns all articles ordered by id DESC.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM articles ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_published(article_id):
    """
    Marks an article as published.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE articles SET is_published = 1 WHERE id = ?", (article_id,))
    conn.commit()
    conn.close()
