import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import time
import io
from backend.app.core.database import get_connection


def pandas_type_to_sql(dtype) -> str:
    """
    Converts a pandas data type to a PostgreSQL data type.
    """
    dtype_str = str(dtype)
    if "int" in dtype_str:
        return "BIGINT"
    elif "float" in dtype_str:
        return "DOUBLE PRECISION"
    elif "datetime" in dtype_str:
        return "TIMESTAMP"
    elif "bool" in dtype_str:
        return "BOOLEAN"
    else:
        return "TEXT"


def clean_column_name(col: str) -> str:
    """
    Cleans a column name to be valid in PostgreSQL.
    Replaces spaces and special characters with underscores.
    """
    import re
    col = col.strip().lower()
    col = re.sub(r"[^a-z0-9_]", "_", col)
    if col[0].isdigit():
        col = "col_" + col
    return col


def load_csv_to_db(file_content: bytes, filename: str) -> dict:
    """
    Takes a CSV file as bytes, reads it with pandas,
    creates a PostgreSQL table and loads all data into it.
    Returns the table name and schema info.
    """
    try:
        # Step 1: Read the CSV with pandas
        df = pd.read_csv(io.BytesIO(file_content))

        if df.empty:
            return {"status": "error", "message": "The CSV file is empty"}

        if len(df.columns) == 0:
            return {"status": "error", "message": "No columns found in CSV"}

        # Step 2: Clean column names
        df.columns = [clean_column_name(col) for col in df.columns]

        # Step 3: Generate a unique table name using timestamp
        timestamp = int(time.time())
        base_name = filename.replace(".csv", "").lower()
        base_name = clean_column_name(base_name)
        table_name = f"upload_{timestamp}_{base_name}"

        # Step 4: Build CREATE TABLE SQL
        columns_sql = []
        for col in df.columns:
            sql_type = pandas_type_to_sql(df[col].dtype)
            columns_sql.append(f"{col} {sql_type}")

        create_sql = f"""
            CREATE TABLE {table_name} (
                _row_id SERIAL PRIMARY KEY,
                {", ".join(columns_sql)}
            );
        """

        # Step 5: Connect and create the table
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(create_sql)
        conn.commit()

        # Step 6: Insert all rows
        cols = list(df.columns)
        placeholders = ", ".join(["%s"] * len(cols))
        col_names = ", ".join(cols)
        insert_sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"

        # Replace NaN with None for proper NULL handling
        df = df.where(pd.notna(df), None)

        rows = [tuple(row) for row in df.itertuples(index=False)]
        cursor.executemany(insert_sql, rows)
        conn.commit()

        cursor.close()
        conn.close()

        # Step 7: Build schema description for LLM
        schema_lines = [f"TABLE: {table_name}"]
        schema_lines.append("COLUMNS:")
        for col in df.columns:
            sql_type = pandas_type_to_sql(df[col].dtype)
            schema_lines.append(f"  - {col} ({sql_type})")

        schema_text = "\n".join(schema_lines)

        return {
            "status": "success",
            "table_name": table_name,
            "row_count": len(df),
            "columns": list(df.columns),
            "schema_text": schema_text,
            "message": f"Successfully loaded {len(df)} rows into table {table_name}"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_uploaded_tables() -> dict:
    """
    Returns all uploaded CSV tables currently in the database.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT table_name, 
                   pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE 'upload_%'
            ORDER BY table_name DESC;
        """)
        tables = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return {"status": "success", "tables": tables}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def drop_uploaded_table(table_name: str) -> dict:
    """
    Drops an uploaded CSV table from the database.
    Only works on tables that start with 'upload_' for safety.
    """
    try:
        if not table_name.startswith("upload_"):
            return {
                "status": "error",
                "message": "Can only delete uploaded tables"
            }

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        conn.commit()
        cursor.close()
        conn.close()

        return {"status": "success", "message": f"Table {table_name} deleted"}
    except Exception as e:
        return {"status": "error", "message": str(e)}