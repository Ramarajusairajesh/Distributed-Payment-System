import logging
import os
import uuid
import httpx
import json
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from jose import JWTError

from app.common.database.db import get_db
from app.common.database.init_db import init_db
from app.common.models.users import User
from app.common.models.accounts import Account, AccountStatus, AccountType
from app.common.schemas.accounts import (
    AccountCreate, 
    AccountResponse, 
    AccountUpdate, 
    AccountListResponse,
    BalanceUpdate
)
from app.common.utils.distributed import distributed_lock
from app.common.utils.kafka_client import kafka_client

# Setup logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Account Service",
    description="Account management service for the Distributed Payment System",
    version="1.0.0",
)

# Auth service URL
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8001")

# Initialize database
@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Account Service started")

# Function to get current user from token
async def get_current_user(authorization: str = Header(...)):
    """
    Get the current user from the authorization header by validating with auth service.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    
    # Validate token with auth service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/validate-token",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            user_data = response.json()
            return user_data
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is unavailable",
        )

# Function to generate account number
def generate_account_number():
    """
    Generate a unique account number.
    """
    return f"ACC-{uuid.uuid4().hex[:8].upper()}"

# Create account endpoint
@app.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: AccountCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new account for the authenticated user.
    """
    # Create new account
    account = Account(
        user_id=current_user["id"],
        account_number=generate_account_number(),
        account_type=account_data.account_type,
        currency=account_data.currency
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    # Notify account creation via Kafka
    account_dict = {
        "id": account.id,
        "user_id": account.user_id,
        "account_number": account.account_number,
        "account_type": account.account_type.value,
        "status": account.status.value,
        "currency": account.currency,
        "created_at": account.created_at.isoformat()
    }
    
    kafka_client.produce_message(
        "account_events",
        {
            "event_type": "account_created",
            "data": account_dict
        },
        key=account.id
    )
    
    return account

# Get all accounts for the current user
@app.get("/accounts", response_model=AccountListResponse)
async def get_user_accounts(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all accounts for the authenticated user.
    """
    accounts = db.query(Account).filter(Account.user_id == current_user["id"]).all()
    return {"accounts": accounts, "total": len(accounts)}

# Get account by ID
@app.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get an account by ID.
    """
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user["id"]
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
        
    return account

# Update account
@app.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    account_update: AccountUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an account.
    """
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user["id"]
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
        
    # Update account fields if provided
    if account_update.account_type is not None:
        account.account_type = account_update.account_type
    
    if account_update.status is not None:
        account.status = account_update.status
    
    if account_update.currency is not None:
        account.currency = account_update.currency
        
    db.commit()
    db.refresh(account)
    
    # Notify account update via Kafka
    account_dict = {
        "id": account.id,
        "user_id": account.user_id,
        "account_type": account.account_type.value,
        "status": account.status.value,
        "currency": account.currency,
        "updated_at": account.updated_at.isoformat()
    }
    
    kafka_client.produce_message(
        "account_events",
        {
            "event_type": "account_updated",
            "data": account_dict
        },
        key=account.id
    )
    
    return account

# Deposit funds
@app.post("/accounts/{account_id}/deposit", response_model=AccountResponse)
@distributed_lock(key_prefix="account_lock")
async def deposit_funds(
    account_id: str,
    deposit_data: BalanceUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deposit funds to an account.
    """
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == current_user["id"]
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
        
    if account.status != AccountStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot deposit to {account.status.value} account"
        )
        
    # Update balance
    account.balance += deposit_data.amount
    db.commit()
    db.refresh(account)
    
    # Notify balance update via Kafka
    balance_event = {
        "account_id": account.id,
        "user_id": account.user_id,
        "amount": deposit_data.amount,
        "balance": account.balance,
        "currency": account.currency,
        "operation": "deposit",
        "description": deposit_data.description or "Deposit",
        "timestamp": account.updated_at.isoformat()
    }
    
    kafka_client.produce_message(
        "balance_events",
        {
            "event_type": "balance_updated",
            "data": balance_event
        },
        key=account.id
    )
    
    return account

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "service": "account"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8002"))) 