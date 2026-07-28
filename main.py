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

# --- STAGE 2 ENDPOINTS: READ FROM POSTGRES ---

# 1. Fetch all tasks from PostgreSQL
@app.get("/tasks")
def get_all_tasks():
    """Retrieve all task records from the PostgreSQL tasks table."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM tasks ORDER BY id ASC;")
        rows = cursor.fetchall()
    conn.close()
    return rows


# 2. Fetch a single task by ID from PostgreSQL
@app.get("/tasks/{task_id}")
def get_single_task(task_id: int):
    """Fetch a single task record by ID using a parameterized query."""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Pass task_id in a tuple to %s placeholder safely
        cursor.execute("SELECT * FROM tasks WHERE id = %s;", (task_id,))
        task = cursor.fetchone()
    conn.close()
    
    # Guard Rule: If no row matches that ID, return 404
    if task is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Task not found"}
        )
        
    return task