# server/config.py
from pathlib import Path
import os

BASE = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE / "mess.db")

# secrets - override in environment for prod
JWT_SECRET = os.environ.get("MESS_JWT_SECRET", "change_this_random_secret_now")
JWT_ALGO = "HS256"
JWT_EXP_DAYS = int(os.environ.get("JWT_EXP_DAYS", "7"))
