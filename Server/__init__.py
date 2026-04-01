# server/__init__.py
# make this a package, optionally expose create_app if you prefer flask factory pattern
from .server import app  # if server.py defines app at module level
