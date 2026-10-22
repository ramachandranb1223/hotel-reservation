import os
import secrets
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    # A shared, hardcoded default secret key would let anyone who has seen this
    # source forge a session cookie for any account, so there is no usable
    # default: set SECRET_KEY in .env. A random key is generated as a fallback,
    # which is safe but logs everyone out whenever the server restarts.
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)

    # Debug defaults to OFF. Flask's debugger exposes an interactive Python
    # console on error, so it must never be on outside local development.
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")

    # Bind to localhost by default; 0.0.0.0 exposes the app to the whole network.
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 5000))
    
    # Oracle Database Credentials
    ORACLE_USER = os.getenv("ORACLE_USER", "hotel_admin")
    ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "hotel_password_123")
    ORACLE_DSN = os.getenv("ORACLE_DSN", "localhost:1521/XEPDB1")
    ORACLE_WALLET_DIR = os.getenv("ORACLE_WALLET_DIR", None)
    ORACLE_WALLET_PASSWORD = os.getenv("ORACLE_WALLET_PASSWORD", None)
    
    # DB mode: 'oracle', 'sqlite', or 'auto' (tries Oracle first, graceful fallback for offline dev)
    USE_ORACLE_DB = os.getenv("USE_ORACLE_DB", "auto").lower()

    # Session settings
    SESSION_COOKIE_NAME = "grandluxe_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Send the session cookie over HTTPS only when not in debug/local dev.
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1", "yes")
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
