from backend.app.core.database import get_connection
from psycopg2.extras import RealDictCursor


def save_query(question: str, sql: str, row_count: int, status: str, error_message: str = None) -> dict:
    """
    Saves a query and its result to the query_history table.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            INSERT INTO query_history 
                (question, sql_generated, row_count, status, error_message)
            VALUES 
                (%s, %s, %s, %s, %s)
            RETURNING id, created_at;
        """, (question, sql, row_count, status, error_message))

        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        return {
            "status": "success",
            "id": result["id"],
            "created_at": str(result["created_at"])
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_history(limit: int = 20) -> dict:
    """
    Returns the most recent queries from the history table.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT 
                id,
                question,
                sql_generated,
                row_count,
                status,
                error_message,
                created_at
            FROM query_history
            ORDER BY created_at DESC
            LIMIT %s;
        """, (limit,))

        rows = [dict(row) for row in cursor.fetchall()]

        # Convert timestamps to strings for JSON serialization
        for row in rows:
            row["created_at"] = str(row["created_at"])

        cursor.close()
        conn.close()

        return {
            "status": "success",
            "history": rows,
            "count": len(rows)
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_stats() -> dict:
    """
    Returns summary statistics about query history.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                COUNT(*) as total_queries,
                COUNT(*) FILTER (WHERE status = 'success') as successful_queries,
                COUNT(*) FILTER (WHERE status = 'error') as failed_queries,
                ROUND(
                    COUNT(*) FILTER (WHERE status = 'success') * 100.0 / 
                    NULLIF(COUNT(*), 0), 1
                ) as success_rate
            FROM query_history;
        """)

        stats = dict(cursor.fetchone())
        cursor.close()
        conn.close()

        return {"status": "success", "stats": stats}

    except Exception as e:
        return {"status": "error", "message": str(e)}