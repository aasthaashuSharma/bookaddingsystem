# server/add_user.py
import sqlite3
from werkzeug.security import generate_password_hash
from pathlib import Path
from config import DB_PATH

DB = Path(DB_PATH)

def add_user(email, name, raw_password, hostel_type=None, hostel_name=None, room=None, is_admin=0):
    pwd_hash = generate_password_hash(raw_password)
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users (email, name, password_hash, hostel_type, hostel_name, room, is_admin)
            VALUES (?,?,?,?,?,?,?)
        """, (email, name, pwd_hash, hostel_type, hostel_name, room, is_admin))
        conn.commit()
        print(f"[OK] Added user: {email}")
    except Exception as e:
        print("[ERROR]", e)
    finally:
        conn.close()

if __name__ == "__main__":
    # Interactive mode
    print("\n--- Add New User ---")
    e = input("Email: ").strip()
    n = input("Name: ").strip()
    p = input("Password: ").strip()
    ht = input("Hostel Type (boys/girls): ").strip() or None
    hn = input("Hostel Name: ").strip() or None
    rm = input("Room No: ").strip() or None
    
    add_user(e, n, p, ht, hn, rm)
