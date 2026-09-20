import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "grandluxe-default-key-dev-12345")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
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
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
