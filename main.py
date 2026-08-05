import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Auth API Practice")


class UserAuth(BaseModel):
    email: str
    password: str


@app.get("/")
def root():
    return {"message": "Server running and connected to Supabase"}


# ---------------------------------------------------------
# STAGE 1: SIGN UP
# ---------------------------------------------------------
@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(credentials: UserAuth):
    if not credentials.email.strip() or not credentials.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required",
        )

    try:
        response = supabase.auth.sign_up(
            {"email": credentials.email, "password": credentials.password}
        )

        user_info = None
        if response.user:
            user_info = {
                "id": str(response.user.id),
                "email": response.user.email,
            }

        return {"message": "User created successfully", "user": user_info}
    except Exception as e:
        # PRINT THE EXACT ERROR TO YOUR TERMINAL
        print("\n--- SUPABASE SIGNUP ERROR ---")
        print(f"Error details: {e}")
        print("-----------------------------\n")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supabase Error: {str(e)}",
        )


# ---------------------------------------------------------
# STAGE 1: LOG IN
# ---------------------------------------------------------
@app.post("/auth/login", status_code=status.HTTP_200_OK)
def login(credentials: UserAuth):
    if not credentials.email.strip() or not credentials.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required",
        )

    try:
        response = supabase.auth.sign_in_with_password(
            {"email": credentials.email, "password": credentials.password}
        )

        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid login credentials",
            )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer",
        }
    except HTTPException:
        raise
    except Exception as e:
        print("\n--- SUPABASE LOGIN ERROR ---")
        print(f"Error details: {e}")
        print("----------------------------\n")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login credentials",
        )