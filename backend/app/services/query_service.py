from backend.app.core.database import get_connection
from psycopg2.extras import RealDictCursor

def execute_query(sql: str) -> dict:
    """
    Executes a SQL query against the database and returns the results.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Execute the query
        cursor.execute(sql)

        # Fetch all results
        rows = cursor.fetchall()

        # Convert to a list of plain dictionaries
        results = [dict(row) for row in rows]

        # Get column names
        columns = [desc[0] for desc in cursor.description]

        cursor.close()
        conn.close()

        return {
            "status": "success",
            "columns": columns,
            "rows": results,
            "row_count": len(results)
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


def generate_and_execute(question: str) -> dict:
    """
    Full pipeline: takes a natural language question,
    generates SQL, executes it, and returns the results.
    """
    from backend.app.services.llm_service import generate_sql

    # Step 1: Generate the SQL
    sql_result = generate_sql(question)
    if sql_result["status"] != "success":
        return sql_result

    sql = sql_result["sql"]

    # Step 2: Execute the SQL
    execution_result = execute_query(sql)
    if execution_result["status"] != "success":
        return {
            "status": "error",
            "question": question,
            "sql": sql,
            "message": execution_result["message"]
        }

    # Step 3: Return everything together
    return {
        "status": "success",
        "question": question,
        "sql": sql,
        "model": sql_result["model"],
        "columns": execution_result["columns"],
        "rows": execution_result["rows"],
        "row_count": execution_result["row_count"]
    }