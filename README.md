# NL-SQL Engine

A natural language to SQL query engine that lets users ask questions about a database in plain English and get real results back instantly.

Built as a B.Tech final year project to demonstrate end-to-end data engineering, LLM integration, and full-stack development skills.

---

## Demo

**Ask:** `Show me the top 5 products by unit price`

**Generated SQL:**

    SELECT
      product_name,
      unit_price
    FROM products
    ORDER BY
      unit_price DESC
    LIMIT 5

**Result:**

| product_name | unit_price |
|---|---|
| Côte de Blaye | 263.5 |
| Thüringer Rostbratwurst | 123.79 |
| Mishi Kobe Niku | 97 |
| Sir Rodney's Marmalade | 81 |
| Carnarvon Tigers | 62.5 |

---

## Architecture

    User (React UI)
          ↓
    FastAPI Backend
          ↓
    LLM Service (Groq - LLaMA 3.1)
          ↓
    SQL Validator (sqlglot)
          ↓  ← self-correction loop if invalid
    Query Executor
          ↓
    PostgreSQL (Northwind dataset)
          ↓
    Results + History saved
          ↓
    React Frontend (table display)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Axios |
| Backend | FastAPI, Python 3.12 |
| LLM | Groq API (LLaMA 3.1 8B) |
| SQL Validation | sqlglot |
| Database | PostgreSQL 16 |
| Dataset | Northwind (14 tables, ~2000 rows) |

---

## Key Features

- **Natural language to SQL** — converts plain English questions into valid PostgreSQL queries
- **Schema-aware** — automatically reads the full database schema before generating SQL
- **Self-correction** — if generated SQL fails validation, automatically sends the error back to the LLM for one correction attempt
- **SQL validation** — uses sqlglot to parse and validate all generated SQL before execution
- **Query history** — every query is logged to PostgreSQL with timestamp, status, and row count
- **Accuracy tracking** — `/history/stats` endpoint tracks success rate across all queries
- **REST API** — fully documented FastAPI backend with auto-generated Swagger UI at `/docs`

---

## Project Structure

    nl-sql-engine/
    ├── backend/
    │   └── app/
    │       ├── core/
    │       │   └── database.py            # PostgreSQL connection
    │       ├── services/
    │       │   ├── llm_service.py         # Groq LLM + self-correction
    │       │   ├── schema_service.py      # Schema introspection
    │       │   ├── query_service.py       # SQL execution + history
    │       │   ├── validation_service.py  # sqlglot validation
    │       │   └── history_service.py     # Query history CRUD
    │       └── main.py                    # FastAPI routes
    ├── frontend/
    │   └── src/
    │       ├── App.js                     # Main React component
    │       └── App.css                    # Styles
    ├── data/
    │   └── northwind.sql                  # Database dump
    ├── .env                               # API keys (not committed)
    ├── requirements.txt                   # Python dependencies
    └── README.md

---

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 16+
- Groq API key (free at https://console.groq.com)

### 1. Clone the repository

    git clone https://github.com/diya019-git/nl-sql-engine.git
    cd nl-sql-engine

### 2. Set up Python environment

    python -m venv venv
    venv\Scripts\Activate.ps1
    pip install -r requirements.txt

### 3. Set up PostgreSQL

    psql -U postgres -c "CREATE DATABASE nlsql;"
    psql -U postgres -d nlsql -f data/northwind.sql

### 4. Configure environment variables

Create a `.env` file in the project root:

    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=nlsql
    DB_USER=postgres
    DB_PASSWORD=your_password
    GROQ_API_KEY=your_groq_api_key

### 5. Run the backend

    uvicorn backend.app.main:app --reload

### 6. Run the frontend

    cd frontend
    npm install
    npm start

### 7. Open the app

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/db/tables` | List all tables |
| GET | `/db/schema` | Full schema as JSON |
| GET | `/db/schema/text` | Schema formatted for LLM |
| POST | `/query/generate` | Generate SQL from question |
| POST | `/query/execute` | Execute raw SQL |
| POST | `/query/ask` | Full pipeline: question → results |
| POST | `/query/validate` | Validate SQL with sqlglot |
| GET | `/history` | Last 20 queries |
| GET | `/history/stats` | Success rate and counts |

---

## Sample Questions to Try

- `How many customers are there?`
- `Show me the top 5 products by unit price`
- `Which employee handled the most orders?`
- `What is the total revenue per product category?`
- `Show me all orders placed by customers from Germany`
- `Which shipper delivered the most orders in 1997?`

---

## What I Learned

- How to build a production-style pipeline where schema context is injected into LLM prompts
- How to implement self-correcting LLM pipelines using error feedback loops
- How to use sqlglot for dialect-aware SQL parsing and validation
- How to connect FastAPI with PostgreSQL using psycopg2
- How to measure and track LLM accuracy using execution-match evaluation

---

## Author

**Diya** — B.Tech Final Year Project

GitHub: [@diya019-git](https://github.com/diya019-git)