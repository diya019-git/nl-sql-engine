import sqlglot
import sqlglot.errors

def validate_sql(sql: str) -> dict:
    """
    Uses sqlglot to parse and validate a SQL query.
    Returns whether it is valid and any error details.
    """
    try:
        # Try to parse the SQL using sqlglot
        parsed = sqlglot.parse(sql, dialect="postgres")

        # If parsing returned nothing it is invalid
        if not parsed:
            return {
                "valid": False,
                "error": "Could not parse the SQL query — it may be empty or malformed."
            }

        return {
            "valid": True,
            "error": None,
            "parsed_sql": parsed[0].sql(dialect="postgres")
        }

    except sqlglot.errors.ParseError as e:
        return {
            "valid": False,
            "error": f"SQL syntax error: {str(e)}"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Validation error: {str(e)}"
        }


def clean_sql(sql: str) -> str:
    """
    Cleans and normalizes a SQL query using sqlglot.
    Removes extra whitespace and standardizes formatting.
    """
    try:
        parsed = sqlglot.parse_one(sql, dialect="postgres")
        return parsed.sql(dialect="postgres", pretty=True)
    except Exception:
        # If cleaning fails just return the original
        return sql