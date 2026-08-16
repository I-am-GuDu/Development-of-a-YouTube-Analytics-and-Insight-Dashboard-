"""
PostgreSQL Database Configuration and Connection Manager
"""
import os
import logging
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

def _get_secret(key: str, default=None):
    """Read a secret from st.secrets (Streamlit Cloud) or os.getenv (local)."""
    try:
        import streamlit as st
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)

class DatabaseManager:
    def __init__(self):
        # Try st.secrets first (Streamlit Cloud), then fall back to os.getenv (local .env)
        self.database_url = _get_secret('DATABASE_URL')
        if self.database_url:
            self.connection_string = self.database_url
        else:
            self.db_host = _get_secret('DB_HOST', 'localhost')
            self.db_port = _get_secret('DB_PORT', '5432')
            self.db_name = _get_secret('DB_NAME', 'youtube_analytics')
            self.db_user = _get_secret('DB_USER', 'postgres')
            self.db_password = _get_secret('DB_PASSWORD')
            if not self.db_password:
                raise ValueError("DB_PASSWORD is not set. Add it to your .env file or Streamlit Cloud secrets.")

            # Create connection string
            self.connection_string = f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        
        # Create engine
        self.engine = create_engine(
            self.connection_string,
            pool_pre_ping=True,  # Validate connections before use
            pool_recycle=300,    # Recycle connections every 5 minutes
            echo=False           # Set to True for SQL debugging
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            logger.error("Database connection failed: %s", e)
            return False
    
    def initialize_schema(self):
        """Initialize database schema by executing schema.sql"""
        try:
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            with self.engine.connect() as conn:
                conn.execute(text(schema_sql))
                conn.commit()
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize schema: %s", e)
            raise e


@st.cache_resource(show_spinner=False)
def get_shared_manager() -> DatabaseManager:
    """The one DatabaseManager for the whole app process.

    A DatabaseManager owns a SQLAlchemy Engine, and every Engine owns its own
    connection pool. Building one per rerun (or per user session) meant a fresh
    TCP+TLS+auth handshake to Postgres on first query and an orphaned pool
    afterwards, which also made ``pool_pre_ping`` / ``pool_recycle`` pointless.

    ``st.cache_resource`` is the correct scope here: an Engine is thread-safe and
    intended to be shared process-wide. Sessions are *not*, so callers should
    still create their own via ``get_session()``.
    """
    return DatabaseManager()