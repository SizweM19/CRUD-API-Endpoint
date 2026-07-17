from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI()

# Our In-Memory Database ()
tasks: list[dict] = [
    {"id": 1, "title": "Setup VS Code and Python", "done": True},
    {"id": 2, "title": "Build Stage 0 and 1 endpoints", "done": True},
    {"id": 3, "title": "Complete full CRUD assignment", "done": False},
]

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

