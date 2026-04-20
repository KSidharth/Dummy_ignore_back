
"""
Database initialization script for Windows.
Run this if psql command is not available in PATH.
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection parameters
DB_USER = "postgres"
DB_PASSWORD = "KSR@2010030443"  # Change this to your PostgreSQL password
DB_HOST = "localhost"
DB_PORT = "5432"
NEW_DB_NAME = "logindb"

def create_database():
    """Create the logindb database if it doesn't exist."""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (NEW_DB_NAME,)
        )
        exists = cursor.fetchone()
        
        if exists:
            print(f"Database '{NEW_DB_NAME}' already exists.")
        else:
            # Create database
            cursor.execute(f'CREATE DATABASE {NEW_DB_NAME}')
            print(f"Database '{NEW_DB_NAME}' created successfully!")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Error creating database: {e}")
        return False
    
    return True

def initialize_schema():
    """Initialize database schema by running init_db.sql."""
    try:
        # Connect to the new database
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=NEW_DB_NAME
        )
        
        cursor = conn.cursor()
        
        # Read and execute init_db.sql
        with open('init_db.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
            cursor.execute(sql_script)
        
        conn.commit()
        print("Database schema initialized successfully!")
        print("\nTest user created:")
        print("  Email: test@example.com")
        print("  Password: password123")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Error initializing schema: {e}")
        return False
    except FileNotFoundError:
        print("Error: init_db.sql file not found!")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("PostgreSQL Database Initialization for Login System")
    print("=" * 60)
    print()
    
    # Step 1: Create database
    print("Step 1: Creating database...")
    if not create_database():
        print("\nDatabase creation failed. Exiting.")
        exit(1)
    
    print()
    
    # Step 2: Initialize schema
    print("Step 2: Initializing schema...")
    if not initialize_schema():
        print("\nSchema initialization failed. Exiting.")
        exit(1)
    
    print()
    print("=" * 60)
    print("Database setup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Update .env file with your database credentials")
    print("  2. Run: uvicorn app.main:app --reload")
    print()
