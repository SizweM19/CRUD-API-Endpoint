from fastapi import FastAPI, status, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

# Our In-Memory Database ()
tasks: list[dict] = [
    {"id": 1, "title": "Setup VS Code and Python", "done": True},
    {"id": 2, "title": "Build Stage 0 and 1 endpoints", "done": True},
    {"id": 3, "title": "Complete full CRUD assignment", "done": False},
]

# The Pydantic Model: Defines what the client is allowed to send us
class TaskCreate(BaseModel):
    title: str


# Root Endpoint
# Returns a JSON description of the system metadata

@app. get("/")
def get_root():
    return{
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

# STAGE 1: Health Check Endpoint
# Used by production monitoring systems to verify the server is active
@app.get("/health")
def get_health():
    return {"status": "ok"}


# --- STAGE 2 ENDPOINTS (READ) ---
@app.get("/tasks")
def get_all_tasks():
    return tasks

# 2. Fetch a single, specific task by ID
@app.get("/tasks/{task_id}")
def get_single_task(task_id: int):
    # Loop through our in-memory data store to find a matching ID
    for task in tasks:
        if task["id"] == task_id:
            return task  # Found it! Return the task immediately (Defaults to 200 OK)
            
    # Architectural Guard: If the loop finishes and finds nothing, trigger a 404 response
    return JSONResponse(
        status_code = status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {task_id} not found"}
    )


# --- STAGE 3 ENDPOINT (CREATE) ---
@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(new_task: TaskCreate):
    # Business Rule 1: Input Validation
    # If the title is empty or just white spaces, reject it immediately
    if not new_task.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Title cannot be empty"
        )
        
    # Business Rule 2: Dynamically calculate the next available ID
    next_id = max(task["id"] for task in tasks) + 1 if tasks else 1
    
    # Business Rule 3: Structure the complete task entity
    task_entry = {
        "id": next_id,
        "title": new_task.title,
        "done": False  # New tasks are always incomplete by default
    }
    
    # Save to our in-memory data collection
    tasks.append(task_entry)
    
    # Return the newly created resource back to the client
    return task_entry