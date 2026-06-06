from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.app.core.database import test_connection, get_all_tables
from backend.app.services.schema_service import get_full_schema, format_schema_for_llm
from backend.app.services.llm_service import generate_sql
from backend.app.services.query_service import execute_query, generate_and_execute
from backend.app.services.validation_service import validate_sql, clean_sql
from backend.app.services.history_service import get_history, get_stats
from backend.app.services.csv_service import load_csv_to_db, get_uploaded_tables, drop_uploaded_table
from backend.app.services.csv_query_service import ask_csv

app = FastAPI(
    title="NL-SQL Engine",
    description="Natural Language to SQL query engine",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

class SQLRequest(BaseModel):
    sql: str

class CSVQuestionRequest(BaseModel):
    question: str
    table_name: str
    schema_text: str

@app.get("/")
def root():
    return {"message": "NL-SQL Engine is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "0.1.0"}

@app.get("/db/test")
def database_test():
    """Test the database connection."""
    return test_connection()

@app.get("/db/tables")
def list_tables():
    """List all tables in the database."""
    return get_all_tables()

@app.get("/db/schema")
def get_schema():
    """Get the full database schema as structured JSON."""
    return get_full_schema()

@app.get("/db/schema/text")
def get_schema_text():
    """Get the database schema formatted as plain text for the LLM."""
    result = get_full_schema()
    if result["status"] == "success":
        formatted = format_schema_for_llm(result["schema"])
        return {"status": "success", "schema_text": formatted}
    return result

@app.post("/query/generate")
def generate_query(request: QuestionRequest):
    """Take a natural language question and return a validated SQL query."""
    return generate_sql(request.question)

@app.post("/query/execute")
def execute_sql(request: SQLRequest):
    """Execute a raw SQL query and return the results."""
    return execute_query(request.sql)

@app.post("/query/ask")
def ask_question(request: QuestionRequest):
    """Full pipeline: natural language question → SQL → executed results."""
    return generate_and_execute(request.question)

@app.post("/query/validate")
def validate_query(request: SQLRequest):
    """Validate a SQL query using sqlglot without executing it."""
    return validate_sql(request.sql)

@app.get("/history")
def query_history():
    """Get the most recent 20 queries from history."""
    return get_history()

@app.get("/history/stats")
def query_stats():
    """Get summary statistics about query history."""
    return get_stats()

@app.post("/csv/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file and load it into the database."""
    if not file.filename.endswith(".csv"):
        return {"status": "error", "message": "Only CSV files are allowed"}

    content = await file.read()

    if len(content) > 10 * 1024 * 1024:
        return {"status": "error", "message": "File too large. Maximum size is 10MB"}

    return load_csv_to_db(content, file.filename)

@app.post("/csv/ask")
def ask_csv_question(request: CSVQuestionRequest):
    """Ask a natural language question about an uploaded CSV table."""
    return ask_csv(request.question, request.table_name, request.schema_text)

@app.get("/csv/tables")
def list_csv_tables():
    """List all uploaded CSV tables."""
    return get_uploaded_tables()

@app.delete("/csv/table/{table_name}")
def delete_csv_table(table_name: str):
    """Delete an uploaded CSV table."""
    return drop_uploaded_table(table_name)