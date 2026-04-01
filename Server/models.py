# server/models.py
import sqlite3
from sqlite3 import Connection
from typing import Optional, List, Dict
from config import DB_PATH

def get_db() -> Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def find_user_by_email(email: str):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return user

def create_user(email: str, name: str, password_hash: str, hostel_type=None, hostel_name=None, room=None, is_admin=0):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""INSERT INTO users (email,name,password_hash,hostel_type,hostel_name,room,is_admin)
                   VALUES (?,?,?,?,?,?,?)""", (email, name, password_hash, hostel_type, hostel_name, room, is_admin))
    conn.commit()
    uid = cur.lastrowid
    conn.close()
    return uid

def insert_feedback(user_id: int, meal_type: str, food_rating: int, menu_rating: int, comments: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""INSERT INTO feedback (user_id, meal_type, food_rating, menu_rating, comments)
                   VALUES (?,?,?,?,?)""", (user_id, meal_type, food_rating, menu_rating, comments))
    conn.commit()
    fid = cur.lastrowid
    conn.close()
    return fid

def get_feedbacks_for_user(user_id: int):
    conn = get_db()
    rows = conn.execute("""SELECT f.*, u.name, u.email FROM feedback f
                           LEFT JOIN users u ON f.user_id = u.id
                           WHERE f.user_id = ? ORDER BY f.created_at DESC""", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_feedbacks():
    conn = get_db()
    rows = conn.execute("""SELECT f.*, u.name, u.email FROM feedback f
                           LEFT JOIN users u ON f.user_id = u.id
                           ORDER BY f.created_at DESC""").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_feedback(fid: int):
    conn = get_db()
    conn.execute("DELETE FROM feedback WHERE id = ?", (fid,))
    conn.commit()
    conn.close()

def reply_feedback(fid: int, response: str):
    conn = get_db()
    conn.execute("UPDATE feedback SET response = ? WHERE id = ?", (response, fid))
    conn.commit()
    conn.close()
