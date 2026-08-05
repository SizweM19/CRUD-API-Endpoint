import os
from dotenv import load_dotenv
from fastapi import FastAPI
from supabase import create_client, Client

# Load secrets from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Auth API Practice")

@app.get("/")
def root():
    return {"message": "Server running and connected to Supabase"}