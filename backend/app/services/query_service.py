from backend.app.core.database import get_connection
from psycopg2.extras import RealDictCursor
from backend.app.services.history_service import save_query


def execute_query(sql: str) -> dict:
    """
    Executes a SQL query against the database and returns the results.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(sql)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
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
    Also saves the query to history.
    """
    from backend.app.services.llm_service import generate_sql

    # Step 1: Generate the SQL
    sql_result = generate_sql(question)
    if sql_result["status"] != "success":
        # Save failed attempt to history
        save_query(
            question=question,
            sql=sql_result.get("sql", ""),
            row_count=0,
            status="error",
            error_message=sql_result.get("message", "SQL generation failed")
        )
        return sql_result

    sql = sql_result["sql"]

    # Step 2: Execute the SQL
    execution_result = execute_query(sql)
    if execution_result["status"] != "success":
        # Save failed execution to history
        save_query(
            question=question,
            sql=sql,
            row_count=0,
            status="error",
            error_message=execution_result["message"]
        )
        return {
            "status": "error",
            "question": question,
            "sql": sql,
            "message": execution_result["message"]
        }

    # Step 3: Save successful query to history
    save_query(
        question=question,
        sql=sql,
        row_count=execution_result["row_count"],
        status="success"
    )

    # Step 4: Return everything together
    return {
        "status": "success",
        "question": question,
        "sql": sql,
        "model": sql_result["model"],
        "columns": execution_result["columns"],
        "rows": execution_result["rows"],
        "row_count": execution_result["row_count"]
    }