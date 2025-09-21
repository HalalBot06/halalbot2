import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool
from psycopg2 import OperationalError, DatabaseError
import streamlit as st
from contextlib import contextmanager
import logging
import time
from typing import Optional, List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Production-ready PostgreSQL database manager with connection pooling
    Designed for Railway deployment with fallback for local development
    """
    
    def __init__(self, min_connections: int = 1, max_connections: int = 20):
        """
        Initialize database manager with connection pooling
        
        Args:
            min_connections: Minimum connections in pool
            max_connections: Maximum connections in pool
        """
        self.pool: Optional[SimpleConnectionPool] = None
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.database_url = self._get_database_url()
        self._initialize_pool()
    
    def _get_database_url(self) -> str:
        """
        Get database URL from environment with Railway/local fallback
        
        Returns:
            Database connection URL
            
        Raises:
            ValueError: If no database configuration found
        """
        # Railway provides DATABASE_URL
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            logger.info("Using Railway DATABASE_URL")
            return database_url
        
        # Fallback to individual environment variables for local development
        db_config = {
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'host': os.getenv('DB_HOST', 'localhost'), 
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'halalbot')
        }
        
        # Check if we have minimum required config
        if not db_config['password'] and db_config['host'] == 'localhost':
            logger.warning("No database password set for localhost - this may fail")
        
        database_url = (
            f"postgresql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        
        logger.info(f"Using local database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        return database_url
    
    def _initialize_pool(self, max_retries: int = 3, retry_delay: float = 2.0):
        """
        Initialize connection pool with retry logic
        
        Args:
            max_retries: Maximum connection attempts
            retry_delay: Delay between retry attempts in seconds
            
        Raises:
            OperationalError: If unable to establish database connection
        """
        for attempt in range(max_retries):
            try:
                self.pool = SimpleConnectionPool(
                    minconn=self.min_connections,
                    maxconn=self.max_connections,
                    dsn=self.database_url,
                    # Additional connection parameters for stability
                    connect_timeout=10,
                    application_name='halalbot'
                )
                
                # Test the connection
                with self.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT version();")
                        version = cursor.fetchone()[0]
                        logger.info(f"Database connection established. PostgreSQL version: {version}")
                
                return
                
            except OperationalError as e:
                logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                else:
                    logger.error("Failed to establish database connection after all retries")
                    raise OperationalError(f"Unable to connect to database: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error during database initialization: {e}")
                raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for safe database connections
        
        Yields:
            psycopg2.connection: Database connection from pool
            
        Raises:
            OperationalError: If unable to get connection from pool
        """
        conn = None
        try:
            if not self.pool:
                raise OperationalError("Database pool not initialized")
            
            conn = self.pool.getconn()
            
            if conn is None:
                raise OperationalError("Unable to get connection from pool")
            
            # Test connection is still alive
            if conn.closed:
                logger.warning("Got closed connection from pool, recreating...")
                self.pool.putconn(conn, close=True)
                conn = self.pool.getconn()
            
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
                logger.error(f"Database error, rolling back transaction: {e}")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)
    
    def execute_query(self, 
                     query: str, 
                     params: Optional[tuple] = None, 
                     fetch: bool = False,
                     fetch_one: bool = False) -> Any:
        """
        Execute a single database query
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            fetch: Whether to fetch and return results
            fetch_one: Whether to fetch only one result
            
        Returns:
            Query results if fetch=True, otherwise number of affected rows
            
        Raises:
            DatabaseError: If query execution fails
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    
                    if fetch_one:
                        result = cursor.fetchone()
                        conn.commit()
                        return result
                    elif fetch:
                        result = cursor.fetchall()
                        conn.commit()
                        return result
                    else:
                        conn.commit()
                        return cursor.rowcount
                        
        except Exception as e:
            logger.error(f"Query execution failed: {query[:100]}... Error: {e}")
            raise DatabaseError(f"Query execution failed: {e}")
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        Execute query with multiple parameter sets (batch insert/update)
        
        Args:
            query: SQL query string with placeholders
            params_list: List of parameter tuples
            
        Returns:
            Number of affected rows
            
        Raises:
            DatabaseError: If batch execution fails
        """
        if not params_list:
            logger.warning("execute_many called with empty params_list")
            return 0
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.executemany(query, params_list)
                    conn.commit()
                    return cursor.rowcount
                    
        except Exception as e:
            logger.error(f"Batch execution failed: {query[:100]}... Error: {e}")
            raise DatabaseError(f"Batch execution failed: {e}")
    
    def check_tables_exist(self) -> Tuple[bool, List[str]]:
        """
        Check if all required tables exist in the database
        
        Returns:
            Tuple of (all_exist: bool, missing_tables: List[str])
        """
        required_tables = [
            'users', 
            'invite_codes', 
            'documents', 
            'search_queries', 
            'feedback',
            'blocked_queries'
        ]
        
        try:
            query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = ANY(%s)
            """
            
            existing_tables = self.execute_query(query, (required_tables,), fetch=True)
            existing_names = {table['table_name'] for table in existing_tables}
            
            missing_tables = [table for table in required_tables if table not in existing_names]
            
            logger.info(f"Found {len(existing_names)} of {len(required_tables)} required tables")
            if missing_tables:
                logger.info(f"Missing tables: {missing_tables}")
            
            return len(missing_tables) == 0, missing_tables
            
        except Exception as e:
            logger.error(f"Failed to check table existence: {e}")
            return False, required_tables
    
    def setup_database(self):
        """
        Set up complete database schema for HalalBot
        Creates all required tables with proper indexes and constraints
        
        Raises:
            DatabaseError: If schema creation fails
        """
        logger.info("Setting up database schema...")
        
        # Main schema creation
        schema_sql = """
        -- Enable necessary extensions
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            invite_code VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
        
        -- Invite codes table  
        CREATE TABLE IF NOT EXISTS invite_codes (
            code VARCHAR(50) PRIMARY KEY,
            used BOOLEAN DEFAULT FALSE,
            used_by_email VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used_at TIMESTAMP,
            created_by_admin_id INTEGER REFERENCES users(id)
        );
        
        -- Documents table (using JSONB for embeddings instead of vector type)
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            doc_id VARCHAR(255) UNIQUE,
            text TEXT NOT NULL,
            source VARCHAR(255),
            category VARCHAR(50) NOT NULL,
            title TEXT,
            question TEXT,
            answer TEXT,
            page INTEGER,
            doc_type VARCHAR(50),
            embedding_json JSONB,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Search queries log
        CREATE TABLE IF NOT EXISTS search_queries (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            query TEXT NOT NULL,
            results_count INTEGER DEFAULT 0,
            source_filter VARCHAR(50),
            min_score FLOAT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Feedback table
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
            query TEXT NOT NULL,
            feedback_type VARCHAR(10) NOT NULL CHECK (feedback_type IN ('up', 'down')),
            text_hash VARCHAR(64),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Blocked queries log
        CREATE TABLE IF NOT EXISTS blocked_queries (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            query TEXT NOT NULL,
            blocked_reason VARCHAR(255),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        try:
            # Execute schema creation
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(schema_sql)
                    conn.commit()
            
            logger.info("Database schema created successfully")
            
            # Create indexes for performance
            self._create_indexes()
            
            # Create triggers for updated_at
            self._create_triggers()
            
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            raise DatabaseError(f"Failed to setup database schema: {e}")
    
    def _create_indexes(self):
        """Create database indexes for optimal query performance"""
        indexes_sql = """
        -- Performance indexes
        CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
        CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);
        CREATE INDEX IF NOT EXISTS idx_documents_text_search ON documents USING gin(to_tsvector('english', text));
        
        -- Foreign key indexes
        CREATE INDEX IF NOT EXISTS idx_feedback_document_id ON feedback(document_id);
        CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
        CREATE INDEX IF NOT EXISTS idx_search_queries_user_id ON search_queries(user_id);
        CREATE INDEX IF NOT EXISTS idx_blocked_queries_user_id ON blocked_queries(user_id);
        
        -- Timestamp indexes for analytics
        CREATE INDEX IF NOT EXISTS idx_search_queries_timestamp ON search_queries(timestamp);
        CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp);
        CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
        
        -- Composite indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_documents_category_source ON documents(category, source);
        CREATE INDEX IF NOT EXISTS idx_feedback_type_timestamp ON feedback(feedback_type, timestamp);
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(indexes_sql)
                    conn.commit()
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Some indexes could not be created: {e}")
    
    def _create_triggers(self):
        """Create database triggers for automatic timestamp updates"""
        triggers_sql = """
        -- Function to update updated_at timestamp
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        -- Trigger for documents table
        DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
        CREATE TRIGGER update_documents_updated_at
            BEFORE UPDATE ON documents
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(triggers_sql)
                    conn.commit()
            logger.info("Database triggers created successfully")
            
        except Exception as e:
            logger.warning(f"Could not create triggers: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics for monitoring
        
        Returns:
            Dictionary with database statistics
        """
        try:
            stats_query = """
            SELECT 
                (SELECT COUNT(*) FROM users) as user_count,
                (SELECT COUNT(*) FROM documents) as document_count,
                (SELECT COUNT(*) FROM search_queries) as query_count,
                (SELECT COUNT(*) FROM feedback) as feedback_count,
                (SELECT COUNT(*) FROM invite_codes WHERE used = false) as unused_codes,
                (SELECT pg_size_pretty(pg_database_size(current_database()))) as database_size
            """
            
            result = self.execute_query(stats_query, fetch=True, fetch_one=True)
            return dict(result) if result else {}
            
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            return {}
    
    def health_check(self) -> bool:
        """
        Perform database health check
        
        Returns:
            True if database is healthy, False otherwise
        """
        try:
            result = self.execute_query("SELECT 1", fetch=True, fetch_one=True)
            return result is not None
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def close_pool(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            self.pool = None
            logger.info("Database connection pool closed")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None

def get_db_manager() -> DatabaseManager:
    """
    Get or create the global database manager instance
    Thread-safe singleton pattern for Streamlit
    
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager()
    
    return _db_manager

def init_database() -> bool:
    """
    Initialize database for the application
    
    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_db_manager()
        
        # Perform health check
        if not db.health_check():
            logger.error("Database health check failed")
            return False
        
        # Check if tables exist
        tables_exist, missing_tables = db.check_tables_exist()
        
        if not tables_exist:
            logger.info(f"Missing tables: {missing_tables}")
            logger.info("Setting up database schema...")
            db.setup_database()
            
            # Verify setup
            tables_exist, missing_tables = db.check_tables_exist()
            if not tables_exist:
                logger.error(f"Schema setup failed, still missing: {missing_tables}")
                return False
        
        logger.info("Database initialization successful")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

@st.cache_resource
def get_database() -> DatabaseManager:
    """
    Cached database manager for Streamlit applications
    Uses Streamlit's resource caching for efficiency
    
    Returns:
        DatabaseManager instance
        
    Raises:
        Exception: If database initialization fails
    """
    if init_database():
        return get_db_manager()
    else:
        raise Exception("Failed to initialize database connection")

# Cleanup function for graceful shutdown
def cleanup_database():
    """Clean up database connections on application shutdown"""
    global _db_manager
    if _db_manager:
        _db_manager.close_pool()
        _db_manager = None
        logger.info("Database cleanup completed")

# Register cleanup function
import atexit
atexit.register(cleanup_database)