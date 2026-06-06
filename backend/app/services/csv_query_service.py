from groq import Groq
import os
from dotenv import load_dotenv
from backend.app.services.validation_service import validate_sql, clean_sql
from backend.app.core.database import get_connection
from psycopg2.extras import RealDictCursor

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def call_llm(messages: list) -> str:
    """Makes a single call to the Groq LLM and returns the text response."""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0
    )
    return response.choices[0].message.content.strip()


def clean_llm_sql(sql: str) -> str:
    """Removes any markdown or backticks the LLM accidentally added."""
    if sql.startswith("```"):
        sql = sql.split("\n", 1)[1]
    if sql.endswith("```"):
        sql = sql.rsplit("```", 1)[0]
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql


def ask_csv(question: str, table_name: str, schema_text: str) -> dict:
    """
    Takes a natural language question and a CSV table name,
    generates SQL against that specific table and executes it.
    """
    try:
        # Step 1: Build the prompt using the CSV schema
        prompt = f"""You are an expert SQL developer working with a PostgreSQL database.
Your job is to convert natural language questions into correct SQL queries.

The user has uploaded a CSV file which is now stored as a table called: {table_name}

Here is the schema of that table:
{schema_text}

Rules you must follow:
1. Only return the SQL query, nothing else
2. Do not include any explanation or markdown
3. Do not include code blocks or backticks
4. Always use the exact table name: {table_name}
5. Always use lowercase for column names
6. Make sure the query is valid PostgreSQL syntax
7. For string comparisons always use case-insensitive matching with ILIKE or LOWER()
8. Ignore the _row_id column unless specifically asked about it

Question: {question}

SQL Query:"""

        messages = [
            {
                "role": "system",
                "content": "You are an expert SQL developer. Return only the SQL query with no explanation, no markdown, no backticks."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Step 2: First attempt
        sql = clean_llm_sql(call_llm(messages))

        # Step 3: Validate the SQL
        validation = validate_sql(sql)

        # Step 4: Self-correction if invalid
        if not validation["valid"]:
            correction_messages = messages + [
                {
                    "role": "assistant",
                    "content": sql
                },
                {
                    "role": "user",
                    "content": f"""The SQL query you generated has an error:
{validation["error"]}

Please fix the SQL query. Return only the corrected SQL with no explanation."""
                }
            ]

            sql = clean_llm_sql(call_llm(correction_messages))
            validation = validate_sql(sql)

            if not validation["valid"]:
                return {
                    "status": "error",
                    "question": question,
                    "sql": sql,
                    "message": f"Could not generate valid SQL: {validation['error']}"
                }

        # Step 5: Clean the SQL
        sql = clean_sql(sql)

        # Step 6: Execute the SQL
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        # Convert to plain dicts and handle NaN/None values
        results = []
        for row in rows:
            clean_row = {}
            for key, value in dict(row).items():
                if value != value:  # NaN check
                    clean_row[key] = None
                else:
                    clean_row[key] = value
            results.append(clean_row)
        
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()

        return {
            "status": "success",
            "question": question,
            "sql": sql,
            "table_name": table_name,
            "columns": columns,
            "rows": results,
            "row_count": len(results),
            "model": "llama-3.1-8b-instant"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}