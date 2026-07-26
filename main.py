import sqlite3
from fastapi import FastAPI, status, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

DB_FILE = "tasks.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Setup VS Code and Python", 1),
                ("Build Stage 0 and 1 endpoints", 1),
                ("Complete full CRUD assignment", 0)
            ]
        )
        conn.commit()
    conn.close()

init_db()

# --- PYDANTIC MODELS ---
class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str
    done: bool


# --- STAGE 1 (WEEK 2) ENDPOINTS ---
@app.get("/")
def get_root():
    """Fetch API metadata and available base resource endpoints."""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def get_health():
    """Verify the server operational status for monitoring infrastructure."""
    return {"status": "ok"}


# --- STAGE 1 (WEEK 3) ENDPOINTS: READ FROM DATABASE ---

# 1. Fetch all tasks directly from SQLite
@app.get("/tasks")
def get_all_tasks():
    """Retrieve all task records from the tasks.db SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()
    
    conn.close()  # Clean up database resources
    
    # Convert sqlite3.Row objects into standard dictionaries
    return [dict(row) for row in rows]


# 2. Fetch a single task by ID from SQLite
@app.get("/tasks/{task_id}")
def get_single_task(task_id: int):
    """Fetch a single task record by its ID using a parameterized query."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Use ? placeholder and pass (task_id,) as a tuple for security
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    
    conn.close()  # Clean up database resources
    
    # Guard Rule: If no row matches that ID, return 404
    if row is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {task_id} not found"}
        )
        
    return dict(row)

# --- STAGE 2 (WEEK 3) ENDPOINT: INSERT INTO DATABASE ---

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(new_task: TaskCreate):
    """Insert a new task directly into the SQLite database with validation."""
    # Input Validation: Missing or whitespace-only title returns 400 Bad Request
    if not new_task.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Title cannot be empty"
        )
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Execute parameterized INSERT query (done defaults to 0 / False)
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (new_task.title.strip(), 0)
    )
    
    # Save the transaction permanently to tasks.db disk file
    conn.commit()
    
    # Retrieve the unique ID generated automatically by SQLite
    new_id = cursor.lastrowid
    
    conn.close()
    
    # Return 201 Created with the new task representation
    return {
        "id": new_id,
        "title": new_task.title.strip(),
        "done": False
    }

# --- STAGE 3 (WEEK 3) ENDPOINTS: UPDATE & DELETE WITH SQL ---

# 1. Update an existing task in SQLite
@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_fields: TaskUpdate):
    """Update an existing task in the tasks.db SQLite database."""
    # Input Validation: Empty title returns 400 Bad Request
    if not updated_fields.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot be empty"
        )
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Execute parameterized UPDATE query
    # Note: SQLite stores booleans as integers (1 for True, 0 for False)
    cursor.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (updated_fields.title.strip(), int(updated_fields.done), task_id)
    )
    conn.commit()
    
    # Guard Rule: If 0 rows were updated, the task ID does not exist
    if cursor.rowcount == 0:
        conn.close()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {task_id} not found"}
        )
        
    conn.close()
    
    # Return the newly updated task entity
    return {
        "id": task_id,
        "title": updated_fields.title.strip(),
        "done": updated_fields.done
    }


# 2. Delete an existing task from SQLite
@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    """Permanently delete a task record from tasks.db."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    
    # Guard Rule: If 0 rows were affected, the task ID does not exist
    if cursor.rowcount == 0:
        conn.close()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {task_id} not found"}
        )
        
    conn.close()
    # Success: Return an empty 204 No Content response
    return