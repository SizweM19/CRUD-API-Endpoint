import os
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, status
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
# STAGE 1: SIGN UP & LOG IN
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
            user_info = {"id": str(response.user.id), "email": response.user.email}
        return {"message": "User created successfully", "user": user_info}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login credentials",
        )


# ---------------------------------------------------------
# STAGE 2 & STAGE 3: PUBLIC & VERIFIED PROTECTED ROUTES
# ---------------------------------------------------------
@app.get("/public/info", status_code=status.HTTP_200_OK)
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile", status_code=status.HTTP_200_OK)
def protected_profile(authorization: str = Header(None)):
    # 1. Check if Authorization header is missing or malformed [cite: 1574, 1586]
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token required",
        )

    # 2. Extract token string [cite: 1586]
    token = authorization.split(" ")[1]

    # 3. Ask Supabase to verify the token [cite: 1587-1588]
    try:
        user_response = supabase.auth.get_user(token)
        user = user_response.user

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        # 4. Return safe user metadata on successful verification [cite: 1590]
        return {
            "message": "Access granted",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "created_at": str(user.created_at),
            },
        }
    except Exception:
        # Invalid, expired, or tampered token returns 401 [cite: 1589]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )