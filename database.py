import sqlite3
import hashlib

DB_PATH = 'users.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # users 테이블 생성
    # status: 'Pending', 'Active', 'Rejected'
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(student_id, name, email, phone, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        c.execute('INSERT INTO users (student_id, name, email, phone, password, status) VALUES (?, ?, ?, ?, ?, ?)',
                  (student_id, name, email, phone, hashed_pw, 'Pending'))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(student_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE student_id = ?', (student_id,))
    user = c.fetchone()
    conn.close()
    return user

def authenticate_user(student_id, password):
    user = get_user(student_id)
    if user and user[4] == hash_password(password):
        return user
    return None

def get_pending_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT student_id, name, email, phone, status FROM users WHERE status = 'Pending'")
    users = c.fetchall()
    conn.close()
    return users

def update_user_status(student_id, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET status = ? WHERE student_id = ?', (status, student_id))
    conn.commit()
    conn.close()

def delete_user(student_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE student_id = ?', (student_id,))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
