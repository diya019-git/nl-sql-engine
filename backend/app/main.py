from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.app.core.database import test_connection, get_all_tables
from backend.app.services.schema_service import get_full_schema, format_schema_for_llm
from backend.app.services.llm_service import generate_sql
from backend.app.services.query_service import execute_query, generate_and_execute

app = FastAPI(
    title="NL-SQL Engine",
    description="Natural Language to SQL query engine",
    version="0.1.0"
)

# This allows our React frontend to talk to this backend later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

class SQLRequest(BaseModel):
    sql: str

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
    """Take a natural language question and return a SQL query."""
    return generate_sql(request.question)

@app.post("/query/execute")
def execute_sql(request: SQLRequest):
    """Execute a raw SQL query and return the results."""
    return execute_query(request.sql)

@app.post("/query/ask")
def ask_question(request: QuestionRequest):
    """Full pipeline: natural language question → SQL → executed results."""
    return generate_and_execute(request.question)