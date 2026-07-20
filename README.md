# 📝 Task Management CRUD API

A lightweight, high-performance RESTful CRUD API built with Python and FastAPI for managing a to-do list in-memory.

## 🚀 Quick Start Guide

### Prerequisites
* Python 3.10+
* Virtual Environment (optional but recommended)

1. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn pydantic
   uvicorn main:app --reload
   ![FastAPI setup command shown in a terminal before launching the local API](image.png)
   ![FastAPI Swagger UI showing endpoints GET /, GET /health, GET /tasks, POST /tasks, GET /tasks/{task_id}, PUT /tasks/{task_id}, DELETE /tasks/{task_id} in a browser interface](Screenshot 2026-07-20 202356.png)