# server/server.py
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import jwt, datetime
from functools import wraps
from flask_cors import CORS
from pathlib import Path
from models import find_user_by_email

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "mess.db"

JWT_SECRET = "change_this_random_secret_before_prod"
JWT_ALGO = "HS256"
JWT_EXP_DAYS = 7

app = Flask(__name__, static_folder=str(BASE / "static"), static_url_path="/")
CORS(app)

hostel_data = {
    "boys": [
        {"name": "Laxmi Bhawan", "warden": "Dr. Manoj Kumar Nanda"},
        {"name": "Saraswati Bhawan", "warden": "Shri Satish Khatak"},
        {"name": "Aryaman Bhawan", "warden": "Dr. Amal Chowdhury"}
    ],
    "girls": [
        {"name": "Vidya Bhawan", "warden": "Ms. Jyoti Chaudhary"},
        {"name": "Sarla Bhawan", "warden": "Ms. Monika Sharma"}
    ]
}

def get_db():
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    return conn

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0] == "Bearer":
                token = parts[1]
        if not token:
            return jsonify({"error": "Token missing"}), 401
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            uid = payload.get("id")
            conn = get_db()
            user = conn.execute("SELECT id,email,name,is_admin,hostel_name,hostel_type,room,avatar,theme FROM users WHERE id = ?", (uid,)).fetchone()
            conn.close()
            if not user:
                return jsonify({"error":"User not found"}), 401
            request.user = dict(user)
        except jwt.ExpiredSignatureError:
            return jsonify({"error":"Token expired"}), 401
        except Exception as e:
            return jsonify({"error":"Invalid token", "msg": str(e)}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/api/hostels", methods=["GET"])
def hostels():
    return jsonify(hostel_data)

@app.route("/api/register", methods=["POST"])
def register():
    data = request.json or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = data.get("name") or email.split("@")[0].upper()
    hostel_type = data.get("hostel_type")
    
    hostel_name = data.get("hostel_name")
    room = data.get("room", "")

    if not email or not password:
        return jsonify({"error":"email & password required"}), 400

    hashed = generate_password_hash(password)
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""INSERT INTO users (email,name,password_hash,hostel_type,hostel_name,room)
                       VALUES (?,?,?,?,?)""", (email, name, hashed, hostel_type, hostel_name, room))
        conn.commit()
        uid = cur.lastrowid
        token = jwt.encode({"id": uid, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXP_DAYS)}, JWT_SECRET, algorithm=JWT_ALGO)
        return jsonify({"token": token, "user": {"id": uid, "email": email, "name": name}})
    except sqlite3.IntegrityError:
        return jsonify({"error":"Email already exists"}), 400
    finally:
        conn.close()

@app.route("/api/login", methods=["POST"])
def login():
    # FIX: call get_json()
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"ok": False, "msg": "Email and password required"}), 400

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user:
        return jsonify({"ok": False, "msg": "Invalid credentials"}), 401

    # check password
    stored_hash = user["password_hash"]
    if not check_password_hash(stored_hash, password):
        return jsonify({"ok": False, "msg": "Invalid credentials"}), 401

    # create token
    payload = {
        "id": user["id"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXP_DAYS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    # PyJWT v2 returns string; if bytes, decode:
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    # build user object without password
    user_dict = dict(user)
    user_dict.pop("password_hash", None)

    return jsonify({"ok": True, "msg": "Login successful", "token": token, "user": user_dict}), 200


@app.route("/api/me", methods=["GET"])
@token_required
def me():
    return jsonify(request.user)

@app.route("/api/feedback", methods=["POST"])
@token_required
def post_feedback():
    data = request.json or {}
    meal_type = data.get("meal_type")
    food_rating = data.get("food_rating")
    menu_rating = data.get("menu_rating")
    comments = data.get("comments", "")

    if not meal_type or not food_rating or not menu_rating:
        return jsonify({"error":"Missing fields"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""INSERT INTO feedback (user_id, meal_type, food_rating, menu_rating, comments)
                   VALUES (?,?,?,?,?)""", (request.user["id"], meal_type, int(food_rating), int(menu_rating), comments))
    conn.commit()
    fid = cur.lastrowid
    conn.close()
    return jsonify({"id": fid, "message":"Feedback saved"}), 201

@app.route("/api/feedback", methods=["GET"])
@token_required
def get_feedback():
    conn = get_db()
    if request.user.get("is_admin"):
        rows = conn.execute("""SELECT f.*, u.name, u.email FROM feedback f
                               LEFT JOIN users u ON f.user_id = u.id
                               ORDER BY f.created_at DESC""").fetchall()
    else:
        rows = conn.execute("""SELECT f.*, u.name FROM feedback f
                               LEFT JOIN users u ON f.user_id = u.id
                               WHERE f.user_id = ?
                               ORDER BY f.created_at DESC""", (request.user["id"],)).fetchall()
    conn.close()
    data = [dict(r) for r in rows]
    return jsonify(data)

@app.route("/api/feedback/<int:fid>", methods=["DELETE"])
@token_required
def del_feedback(fid):
    conn = get_db()
    owner = conn.execute("SELECT user_id FROM feedback WHERE id = ?", (fid,)).fetchone()
    if not owner:
        conn.close()
        return jsonify({"error":"Not found"}), 404
    if not (request.user.get("is_admin") or owner["user_id"] == request.user["id"]):
        conn.close()
        return jsonify({"error":"Forbidden"}), 403
    conn.execute("DELETE FROM feedback WHERE id = ?", (fid,))
    conn.commit()
    conn.close()
    return jsonify({"message":"Deleted"})

@app.route("/api/feedback/<int:fid>/reply", methods=["POST"])
@token_required
def reply_feedback(fid):
    if not request.user.get("is_admin"):
        return jsonify({"error":"Forbidden"}), 403
    data = request.json or {}
    response = data.get("response")
    if not response:
        return jsonify({"error":"response required"}), 400
    conn = get_db()
    conn.execute("UPDATE feedback SET response = ? WHERE id = ?", (response, fid))
    conn.commit()
    conn.close()
    return jsonify({"message":"Response saved"})

# serve frontend static files
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    # try serve static file else index.html
    p = Path(app.static_folder) / path
    if path and p.exists():
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
