# server/init_db.py
import sqlite3
from werkzeug.security import generate_password_hash
from pathlib import Path
from config import DB_PATH

def init():
    db_file = Path(DB_PATH)
    db_file.parent.mkdir(parents=True, exist_ok=True)  # ensure folder exists

    conn = sqlite3.connect(str(db_file))
    c = conn.cursor()

    # users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL,
      password_hash TEXT NOT NULL,
      hostel_type TEXT,
      hostel_name TEXT,
      room TEXT,
      avatar TEXT,
      is_admin INTEGER DEFAULT 0,
      theme TEXT DEFAULT 'light',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    # feedback table
    c.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      meal_type TEXT,
      food_rating INTEGER,
      menu_rating INTEGER,
      comments TEXT,
      response TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )""")

    # food_ratings table
    c.execute("""
    CREATE TABLE IF NOT EXISTS food_ratings (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT,
      category TEXT,
      rating REAL DEFAULT 0,
      votes INTEGER DEFAULT 0
    )""")

    # seed sample foods only if empty
    c.execute("SELECT COUNT(*) FROM food_ratings")
    if c.fetchone()[0] == 0:
        sample = [
            ("Chicken Biryani","Lunch",4.5,10),
            ("Paneer Butter Masala","Dinner",4.2,8),
            ("Masala Dosa","Breakfast",4.7,12),
            ("French Fries","Snacks",3.8,5)
        ]
        c.executemany("INSERT INTO food_ratings (name,category,rating,votes) VALUES (?,?,?,?)", sample)

    # seed admin safely (won't duplicate)
    admin_email = "admin@tits.ac.in"
    c.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
    if c.fetchone() is None:
        admin_hash = generate_password_hash("Admin@123")
        c.execute("""INSERT INTO users (email,name,password_hash,is_admin,hostel_type,hostel_name,room)
                     VALUES (?,?,?,?,?,?,?)""",
                  (admin_email, "Mess Administrator", admin_hash, 1, "admin", "Administration", "Office"))

    conn.commit()
    conn.close()
    print("DB created/updated at:", db_file.resolve())

if __name__ == "__main__":
    init()
