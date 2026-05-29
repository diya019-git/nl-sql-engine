from groq import Groq
import os
from dotenv import load_dotenv
from backend.app.services.schema_service import get_full_schema, format_schema_for_llm
from backend.app.services.validation_service import validate_sql, clean_sql

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


def generate_sql(question: str) -> dict:
    """
    Takes a natural language question and returns a validated SQL query.
    If the first attempt is invalid, automatically tries to self-correct once.
    """
    try:
        # Step 1: Get the schema from the database
        schema_result = get_full_schema()
        if schema_result["status"] != "success":
            return {"status": "error", "message": "Could not fetch schema"}

        # Step 2: Format the schema as text for the LLM
        schema_text = format_schema_for_llm(schema_result["schema"])

        # Step 3: Build the initial prompt
        prompt = f"""You are an expert SQL developer working with a PostgreSQL database.
Your job is to convert natural language questions into correct SQL queries.

Here is the database schema:
{schema_text}

Rules you must follow:
1. Only return the SQL query, nothing else
2. Do not include any explanation or markdown
3. Do not include code blocks or backticks
4. Always use lowercase for table and column names
5. Make sure the query is valid PostgreSQL syntax
6. For string comparisons always use case-insensitive matching with ILIKE or LOWER()

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

        # Step 4: First attempt
        sql = clean_llm_sql(call_llm(messages))

        # Step 5: Validate the SQL
        validation = validate_sql(sql)

        # Step 6: If invalid, try self-correction once
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
                    "message": f"Could not generate valid SQL after self-correction: {validation['error']}"
                }

        # Step 7: Clean and normalize the SQL
        sql = clean_sql(sql)

        return {
            "status": "success",
            "question": question,
            "sql": sql,
            "model": "llama-3.1-8b-instant",
            "validated": True
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}