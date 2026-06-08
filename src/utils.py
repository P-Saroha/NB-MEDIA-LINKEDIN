import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

# Database initialization
DB_PATH = "database.db"

def init_database():
    """Initialize SQLite database for storing posts and data"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Posts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            topic TEXT NOT NULL,
            source TEXT,
            image_ideas TEXT,
            hashtags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'draft'
        )
    ''')
    
    # Research topics table
    c.execute('''
        CREATE TABLE IF NOT EXISTS research_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            source TEXT,
            description TEXT,
            relevance_score FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT 0
        )
    ''')
    
    # Training data table
    c.execute('''
        CREATE TABLE IF NOT EXISTS training_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_content TEXT NOT NULL,
            style_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_post(title: str, content: str, topic: str, source: str = None, 
              image_ideas: str = None, hashtags: str = None, status: str = 'draft') -> int:
    """Save a generated post to database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO posts (title, content, topic, source, image_ideas, hashtags, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, content, topic, source, image_ideas, hashtags, status))
    
    post_id = c.lastrowid
    conn.commit()
    conn.close()
    return post_id

def get_posts(status: str = None, limit: int = 10) -> List[Dict]:
    """Retrieve posts from database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if status:
        c.execute('''
            SELECT id, title, content, topic, source, image_ideas, hashtags, created_at, status
            FROM posts WHERE status = ? ORDER BY created_at DESC LIMIT ?
        ''', (status, limit))
    else:
        c.execute('''
            SELECT id, title, content, topic, source, image_ideas, hashtags, created_at, status
            FROM posts ORDER BY created_at DESC LIMIT ?
        ''', (limit,))
    
    posts = []
    for row in c.fetchall():
        posts.append({
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'topic': row[3],
            'source': row[4],
            'image_ideas': row[5],
            'hashtags': row[6],
            'created_at': row[7],
            'status': row[8]
        })
    
    conn.close()
    return posts

def save_research_topic(topic: str, source: str = None, description: str = None, 
                       relevance_score: float = 0.0) -> int:
    """Save a research topic for later processing"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO research_topics (topic, source, description, relevance_score)
        VALUES (?, ?, ?, ?)
    ''', (topic, source, description, relevance_score))
    
    topic_id = c.lastrowid
    conn.commit()
    conn.close()
    return topic_id

def get_unprocessed_topics(limit: int = 5) -> List[Dict]:
    """Get topics that haven't been processed yet"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT id, topic, source, description, relevance_score
        FROM research_topics WHERE processed = 0
        ORDER BY relevance_score DESC LIMIT ?
    ''', (limit,))
    
    topics = []
    for row in c.fetchall():
        topics.append({
            'id': row[0],
            'topic': row[1],
            'source': row[2],
            'description': row[3],
            'relevance_score': row[4]
        })
    
    conn.close()
    return topics

def mark_topic_processed(topic_id: int):
    """Mark a topic as processed"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE research_topics SET processed = 1 WHERE id = ?', (topic_id,))
    conn.commit()
    conn.close()

def load_config() -> Dict:
    """Load configuration from JSON"""
    config_path = 'config/config.json'
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file not found at {config_path}")
        return {}

def load_style_guide() -> Dict:
    """Load style guide from JSON"""
    style_path = 'config/style_guide.json'
    try:
        with open(style_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Style guide not found at {style_path}")
        return {}

def load_system_prompt() -> str:
    """Load system prompt from file"""
    prompt_path = 'config/system_prompt.txt'
    try:
        with open(prompt_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"System prompt not found at {prompt_path}")
        return ""

# Initialize database on import
if not os.path.exists(DB_PATH):
    init_database()
