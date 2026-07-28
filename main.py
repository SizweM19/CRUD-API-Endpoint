import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from fastapi import FastAPI, status, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 1. Load environment variables from .env file
load_dotenv()

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

# --- DATABASE CONNECTION (STAGE 1) ---
def get_db_connection():
    """Establishes connection to PostgreSQL using psycopg."""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is missing!")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    """Initializes table schema and seeds initial data idempotently on startup."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Create table using Postgres SERIAL auto-increment
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT FALSE
            );
        """)
        
        # Check current row count
        cursor.execute("SELECT COUNT(*) FROM tasks;")
        result = cursor.fetchone()
        count = result["count"] if result else 0
        
        # Seed 3 tasks ONLY if database is empty
        if count == 0:
            cursor.executemany(
                "INSERT INTO tasks (title, done) VALUES (%s, %s);",
                [
                    ("Setup VS Code and Python", True),
                    ("Build Stage 0 and 1 endpoints", True),
                    ("Complete full CRUD assignment", False)
                ]
            )
            conn.commit()
            
    conn.close()

# Initialize database immediately on startup
init_db()


# --- PYDANTIC MODELS ---
class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str
    done: bool


# --- BASE ENDPOINTS ---
@app.get("/")
def get_root():
    """Fetch API metadata."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def get_health():
    """Verify server operational status."""
    return {"status": "ok"}