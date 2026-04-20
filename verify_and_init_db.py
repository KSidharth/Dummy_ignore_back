
"""
Database verification and initialization script.
Checks PostgreSQL connection and initializes schema.
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

# Database connection parameters
DB_USER = "postgres"
DB_PASSWORD = "KSR@2010030443"
DB_HOST = "localhost"
DB_PORT = "5432"
NEW_DB_NAME = "logindb"

def test_postgres_connection():
    """Test connection to PostgreSQL server."""
    try:
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database="postgres"
        )
        conn.close()
        print("✓ PostgreSQL connection successful")
        return True
    except psycopg2.Error as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        print("\nPlease check:")
        print("  1. PostgreSQL is running")
        print("  2. Password is correct in this script")
        print("  3. PostgreSQL is listening on localhost:5432")
        return False

def create_database():
    """Create the logindb database if it doesn't exist."""
    try:
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
            print(f"✓ Database '{NEW_DB_NAME}' already exists")
        else:
            # Create database
            cursor.execute(f'CREATE DATABASE {NEW_DB_NAME}')
            print(f"✓ Database '{NEW_DB_NAME}' created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error with database: {e}")
        return False

def initialize_schema():
    """Initialize database schema by running init_db.sql."""
    try:
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
        print("✓ Database schema initialized successfully")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print("\nCreated tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Verify test user exists
        cursor.execute("SELECT email_id FROM login_user WHERE email_id = 'test@example.com'")
        test_user = cursor.fetchone()
        
        if test_user:
            print("\n✓ Test user created:")
            print("  Email: test@example.com")
            print("  Password: password123")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error initializing schema: {e}")
        return False
    except FileNotFoundError:
        print("✗ Error: init_db.sql file not found!")
        print("   Make sure you're running this from the backend directory")
        return False

def verify_asyncpg_connection():
    """Verify asyncpg can connect (test async connection string)."""
    import asyncio
    import asyncpg
    
    async def test_async():
        try:
            conn = await asyncpg.connect(
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
                database=NEW_DB_NAME
            )
            await conn.close()
            print("✓ Asyncpg connection successful")
            return True
        except Exception as e:
            print(f"✗ Asyncpg connection failed: {e}")
            return False
    
    try:
        return asyncio.run(test_async())
    except Exception as e:
        print(f"✗ Asyncpg test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("PostgreSQL Database Setup and Verification")
    print("=" * 70)
    print()
    
    # Step 1: Test PostgreSQL connection
    print("Step 1: Testing PostgreSQL connection...")
    if not test_postgres_connection():
        print("\n❌ Setup failed: Cannot connect to PostgreSQL")
        sys.exit(1)
    print()
    
    # Step 2: Create database
    print("Step 2: Creating/verifying database...")
    if not create_database():
        print("\n❌ Setup failed: Database creation error")
        sys.exit(1)
    print()
    
    # Step 3: Initialize schema
    print("Step 3: Initializing database schema...")
    if not initialize_schema():
        print("\n❌ Setup failed: Schema initialization error")
        sys.exit(1)
    print()
    
    # Step 4: Verify asyncpg connection
    print("Step 4: Verifying async connection (asyncpg)...")
    if not verify_asyncpg_connection():
        print("\n⚠️  Warning: Asyncpg connection failed")
        print("   The application may not start properly")
    print()
    
    print("=" * 70)
    print("✓ Database setup complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Verify .env file has correct DATABASE_URL")
    print("  2. Run: python -m uvicorn app.main:app --reload")
    print()
    print("If you get connection errors, check:")
    print("  - PostgreSQL is running (pg_ctl status)")
    print("  - Password matches in .env file")
    print("  - Database URL format: postgresql+asyncpg://user:password@host:port/db")
    print()
