import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Auth API Practice")

# Configure HTTPBearer security scheme for Swagger UI padlock icon
security = HTTPBearer()


class UserAuth(BaseModel):
    email: str
    password: str


@app.get("/")
def root():
    return {"message": "Server running and connected to Supabase"}


# ---------------------------------------------------------
# STAGE 5: REUSABLE GUARD WITH HTTPBEARER SECURITY SCHEME
# ---------------------------------------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Dependency that extracts the bearer token and verifies it with Supabase."""
    token = credentials.credentials  # Extract token automatically

    try:
        user_response = supabase.auth.get_user(token)
        user = user_response.user

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


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
# STAGE 4: LOG OUT (PROTECTED)
# ---------------------------------------------------------
@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: dict = Depends(get_current_user)):
    try:
        supabase.auth.sign_out()
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


# ---------------------------------------------------------
# STAGE 2: PUBLIC ROUTE
# ---------------------------------------------------------
@app.get("/public/info", status_code=status.HTTP_200_OK)
def public_info():
    return {"message": "Welcome stranger! This info is public."}


# ---------------------------------------------------------
# STAGE 4 & 5: PROTECTED ROUTES
# ---------------------------------------------------------
@app.get("/protected/profile", status_code=status.HTTP_200_OK)
def protected_profile(current_user: dict = Depends(get_current_user)):
    return {
        "message": "Access granted",
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "created_at": str(current_user.created_at),
        },
    }


@app.get("/protected/dashboard", status_code=status.HTTP_200_OK)
def protected_dashboard(current_user: dict = Depends(get_current_user)):
    return {
        "message": f"Welcome to your dashboard, {current_user.email}!",
        "stats": {"audits_completed": 5, "account_status": "Active"},
    }