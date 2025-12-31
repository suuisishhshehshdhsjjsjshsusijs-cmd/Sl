import os
import sqlite3
from datetime import datetime

DB_PATH = os.getenv("DATABASE_PATH", "./data.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    if row is None: return None
    return {k: row[k] for k in row.keys()}

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            balance REAL DEFAULT 0.0,
            created_at TEXT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name_quad TEXT,
            work_place TEXT,
            id_number TEXT,
            birth_date TEXT,
            job_title TEXT,
            nationality TEXT,
            region TEXT,
            hospital TEXT,
            leave_date TEXT,
            status TEXT DEFAULT 'pending',
            pdf_path TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row_to_dict(row)

def add_user(user_id, username, full_name):
    if not get_user(user_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (user_id, username, full_name, created_at) VALUES (?, ?, ?, ?)", 
                       (user_id, username, full_name, datetime.now().isoformat()))
        conn.commit()
        conn.close()

def update_balance(user_id, amount):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def deduct_balance(user_id, amount):
    user = get_user(user_id)
    if user and user['balance'] >= amount:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()
        return True
    return False

def create_request(user_id, data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
    INSERT INTO requests (
        user_id, full_name_quad, work_place, id_number, birth_date, 
        job_title, nationality, region, hospital, leave_date, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, data['full_name_quad'], data['work_place'], data['id_number'], 
        data['birth_date'], data['job_title'], data['nationality'], 
        data['region'], data['hospital'], data['leave_date'], datetime.now().isoformat()
    ))
    request_id = cur.lastrowid
    conn.commit()
    conn.close()
    return request_id

def update_request_pdf(request_id, pdf_path):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE requests SET pdf_path = ?, status = 'completed' WHERE id = ?", (pdf_path, request_id))
    conn.commit()
    conn.close()

def get_stats():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users"); u = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM requests"); r = cur.fetchone()[0]
    conn.close()
    return u, r

def get_all_users(limit=10):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, full_name, balance FROM users ORDER BY created_at DESC LIMIT ?", (limit,))
    users = cur.fetchall()
    conn.close()
    return users
