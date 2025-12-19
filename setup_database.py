"""
Database setup script - initializes PostgreSQL tables
Run this instead of psql if you don't have psql installed locally
"""
import psycopg2
from psycopg2 import sql

# Database connection parameters
DB_PARAMS = {
    "host": "localhost",
    "port": 5432,
    "user": "appuser",
    "password": "apppass",
    "database": "appdb"
}

def setup_database():
    """Create database and tables"""
    try:
        # First, connect to default postgres database to create ai_app
        conn = psycopg2.connect(
            host=DB_PARAMS["host"],
            port=DB_PARAMS["port"],
            user=DB_PARAMS["user"],
            password=DB_PARAMS["password"],
            database="postgres"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'appdb'")
        if not cursor.fetchone():
            cursor.execute("CREATE DATABASE appdb")
            print("✅ Database 'appdb' created")
        else:
            print("✅ Database 'appdb' already exists")
        
        cursor.close()
        conn.close()
        
        # Now connect to ai_app database and create tables
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Read and execute the SQL setup script
        with open('backend/db_setup.sql', 'r') as f:
            sql_script = f.read()
        
        cursor.execute(sql_script)

        # Ensure conversation history table exists
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_history (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}'::jsonb
            )
            """
        )
        conn.commit()
        
        print("✅ Database tables created successfully")
        
        # Verify tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print(f"✅ Created tables: {[t[0] for t in tables]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up PostgreSQL database...")
    setup_database()
