from backend.app.core.database import get_connection
from psycopg2.extras import RealDictCursor

def get_full_schema():
    """
    Reads every table, column, data type and foreign key
    from the database and returns it as a structured dictionary.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [row["table_name"] for row in cursor.fetchall()]

        schema = {}

        for table in tables:
            # Get all columns for this table
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = %s
                ORDER BY ordinal_position;
            """, (table,))
            
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"],
                    "default": row["column_default"]
                })
            
            schema[table] = {"columns": columns}

        # Get all foreign keys
        cursor.execute("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY';
        """)

        for row in cursor.fetchall():
            table = row["table_name"]
            if table in schema:
                if "foreign_keys" not in schema[table]:
                    schema[table]["foreign_keys"] = []
                schema[table]["foreign_keys"].append({
                    "column": row["column_name"],
                    "references_table": row["foreign_table_name"],
                    "references_column": row["foreign_column_name"]
                })

        cursor.close()
        conn.close()
        return {"status": "success", "schema": schema}

    except Exception as e:
        return {"status": "error", "message": str(e)}


def format_schema_for_llm(schema: dict) -> str:
    """
    Converts the schema dictionary into a clean text format
    that is easy for the LLM to read and understand.
    """
    lines = []
    lines.append("DATABASE SCHEMA (PostgreSQL):")
    lines.append("=" * 40)

    for table_name, table_info in schema.items():
        lines.append(f"\nTABLE: {table_name}")
        lines.append("COLUMNS:")
        
        for col in table_info["columns"]:
            nullable = "NULL" if col["nullable"] == "YES" else "NOT NULL"
            lines.append(f"  - {col['name']} ({col['type']}, {nullable})")
        
        if "foreign_keys" in table_info:
            lines.append("FOREIGN KEYS:")
            for fk in table_info["foreign_keys"]:
                lines.append(
                    f"  - {fk['column']} → "
                    f"{fk['references_table']}.{fk['references_column']}"
                )

    return "\n".join(lines)