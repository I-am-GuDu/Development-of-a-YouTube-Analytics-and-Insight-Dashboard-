"""
PostgreSQL Database Configuration and Connection Manager
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        # Get database credentials from environment variables
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_name = os.getenv('DB_NAME', 'youtube_analytics')
        self.db_user = os.getenv('DB_USER', 'postgres')
        self.db_password = os.getenv('DB_PASSWORD')
        if not self.db_password:
            raise ValueError("DB_PASSWORD environment variable is not set. Please configure it in your .env file.")
        
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
            print(f"Database connection failed: {e}")
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
            print("Database schema initialized successfully")
        except Exception as e:
            print(f"Failed to initialize schema: {e}")
            raise e