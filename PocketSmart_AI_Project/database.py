import sqlite3, hashlib, os, json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / "pocketsmart.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            category TEXT NOT NULL,
            input_json TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        conn.commit()

def hash_password(password):
    return hashlib.sha256((password + os.getenv("PASSWORD_SALT", "pocketsmart")).encode()).hexdigest()

def create_user(name, email, password):
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)",
                (name, email, hash_password(password), datetime.now().isoformat(timespec="seconds"))
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("An account with this email already exists.")

def authenticate_user(email, password):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT name,email FROM users WHERE email=? AND password_hash=?",
            (email, hash_password(password))
        ).fetchone()
        return dict(row) if row else None

def save_history(email, category, input_data, result):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO history(email,category,input_json,result_json,created_at) VALUES(?,?,?,?,?)",
            (email, category, json.dumps(input_data), json.dumps(result), datetime.now().isoformat(timespec="seconds"))
        )
        conn.commit()

def get_history(email, limit=100):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM history WHERE email=? ORDER BY id DESC LIMIT ?",
            (email, limit)
        ).fetchall()
    output = []
    for row in rows:
        item = dict(row)
        item["input"] = json.loads(item.pop("input_json"))
        item["result"] = json.loads(item.pop("result_json"))
        output.append(item)
    return output
