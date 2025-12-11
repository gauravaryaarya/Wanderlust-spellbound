import sqlite3
import json

DB_NAME = "wanderlust.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, 
                  destination TEXT, trip_data JSON, notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def add_user(username, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def check_login(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def save_trip(username, destination, trip_data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO history (username, destination, trip_data, notes) VALUES (?, ?, ?, ?)", 
              (username, destination, json.dumps(trip_data), ""))
    conn.commit()
    conn.close()

def get_history(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, destination, trip_data, notes, created_at FROM history WHERE username=? ORDER BY created_at DESC", (username,))
    rows = c.fetchall()
    conn.close()
    return rows

def update_note(trip_id, note_text):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE history SET notes=? WHERE id=?", (note_text, trip_id))
    conn.commit()
    conn.close()