import logging
import os
from datetime import timedelta

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError

from app.common.database.db import get_db
from app.common.database.init_db import init_db
from app.common.models.users import User
from app.common.schemas.users import UserCreate, UserResponse, Token, UserUpdate, UserInDB
from app.common.utils.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    decode_access_token
)

# Setup logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Auth Service",
    description="Authentication and Authorization service for the Distributed Payment System",
    version="1.0.0",
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize database
@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Auth Service started")

# Function to authenticate user
def authenticate_user(db: Session, username: str, password: str):
    """
    Authenticate a user by username and password.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# Function to get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get the current user from the authentication token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
        
    return user

# Function to get current active user
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    Get the current active user.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Login endpoint
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Get an access token for a user.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=int(os.getenv("JWT_EXPIRATION_MINUTES", "60")))
    
    # Include basic user data in token
    user_data = {
        "id": user.id,
        "username": user.username,
        "is_superuser": user.is_superuser
    }
    
    access_token = create_access_token(
        subject=user.username, 
        expires_delta=access_token_expires,
        additional_data={"user_data": user_data}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Register endpoint
@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    """
    # Check if username exists
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
        
    # Check if email exists
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

# Get user info endpoint
@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get the current user's information.
    """
    return current_user

# Update user info endpoint
@app.put("/users/me", response_model=UserResponse)
async def update_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's information.
    """
    # Update user fields if provided
    if user_update.username is not None and user_update.username != current_user.username:
        # Check if username exists
        db_user = db.query(User).filter(User.username == user_update.username).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        current_user.username = user_update.username
        
    if user_update.email is not None and user_update.email != current_user.email:
        # Check if email exists
        db_user = db.query(User).filter(User.email == user_update.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
        
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
        
    db.commit()
    db.refresh(current_user)
    
    return current_user

# Validate token endpoint
@app.post("/validate-token", response_model=UserInDB)
async def validate_token(current_user: User = Depends(get_current_active_user)):
    """
    Validate a token and return the user information.
    Used by other services to check if a token is valid.
    """
    return current_user

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "service": "auth"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8001"))) 