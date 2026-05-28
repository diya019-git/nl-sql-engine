import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Create and return a PostgreSQL connection."""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    return conn

def test_connection():
    """Test the database connection and return status."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT version();")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return {"status": "connected", "version": result["version"]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_all_tables():
    """Return a list of all table names in the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [row["table_name"] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return {"status": "success", "tables": tables}
    except Exception as e:
        return {"status": "error", "message": str(e)}