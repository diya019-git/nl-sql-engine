from groq import Groq
import os
from dotenv import load_dotenv
from backend.app.services.schema_service import get_full_schema, format_schema_for_llm

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_sql(question: str) -> dict:
    """
    Takes a natural language question and returns a SQL query.
    """
    try:
        # Step 1: Get the schema from the database
        schema_result = get_full_schema()
        if schema_result["status"] != "success":
            return {"status": "error", "message": "Could not fetch schema"}

        # Step 2: Format the schema as text for the LLM
        schema_text = format_schema_for_llm(schema_result["schema"])

        # Step 3: Build the prompt
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

Question: {question}

SQL Query:"""

        # Step 4: Call the Groq API
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert SQL developer. Return only the SQL query with no explanation, no markdown, no backticks."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        # Step 5: Extract the SQL from the response
        sql = response.choices[0].message.content.strip()

        # Step 6: Clean up any accidental backticks or markdown
        if sql.startswith("```"):
            sql = sql.split("\n", 1)[1]
        if sql.endswith("```"):
            sql = sql.rsplit("```", 1)[0]
        sql = sql.replace("```sql", "").replace("```", "").strip()

        return {
            "status": "success",
            "question": question,
            "sql": sql,
            "model": "llama-3.1-8b-instant"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}