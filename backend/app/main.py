from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.database import test_connection, get_all_tables

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