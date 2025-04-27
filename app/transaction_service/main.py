import logging
import os
import uuid
import json
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status, Header, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.common.database.db import get_db
from app.common.database.init_db import init_db
from app.common.models.accounts import Account, AccountStatus
from app.common.models.transactions import Transaction, TransactionStatus, TransactionType
from app.common.schemas.transactions import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
    TransactionListResponse,
    PaymentRequest
)
from app.common.utils.distributed import distributed_lock, is_responsible_for_key, NODE_ID
from app.common.utils.kafka_client import kafka_client, TRANSACTION_TOPIC

# Setup logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Transaction Service",
    description="Transaction processing service for the Distributed Payment System",
    version="1.0.0",
)

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8001")
ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://account_service:8002")

# Initialize database and Kafka consumer
@app.on_event("startup")
async def startup_event():
    init_db()
    
    # Start Kafka consumer for transaction processing
    kafka_client.start_consumer(
        TRANSACTION_TOPIC,
        f"transaction-processor-{NODE_ID}",
        process_transaction_message
    )
    
    logger.info("Transaction Service started")

@app.on_event("shutdown")
async def shutdown_event():
    # Stop Kafka client
    kafka_client.stop()
    logger.info("Transaction Service stopped")

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

# Function to verify account ownership
async def verify_account_ownership(account_id: str, user_id: str):
    """
    Verify that an account belongs to a user.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ACCOUNT_SERVICE_URL}/accounts/{account_id}",
                headers={"Authorization": f"Bearer {user_id}"}  # This is a hack, in real system we'd use a service token
            )
            
            if response.status_code == 404:
                return False
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Account service is unavailable",
                )
                
            account_data = response.json()
            return account_data["user_id"] == user_id
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account service is unavailable",
        )

# Function to update account balance
async def update_account_balance(account_id: str, amount: float, is_debit: bool, description: str = None):
    """
    Update an account balance by calling the account service.
    """
    operation = "withdraw" if is_debit else "deposit"
    endpoint = f"{ACCOUNT_SERVICE_URL}/accounts/{account_id}/{operation}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                json={"amount": abs(amount), "description": description},
                headers={"Authorization": "Bearer service-token"}  # In real system, we'd use a service-to-service token
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to update account balance: {response.text}")
                return False
                
            return True
    except httpx.RequestError as e:
        logger.error(f"Error updating account balance: {e}")
        return False

# Function to process transaction message from Kafka
async def process_transaction_message(message: Dict[str, Any], key: str):
    """
    Process a transaction message received from Kafka.
    """
    transaction_id = message.get("transaction_id")
    
    # Check if this node is responsible for this transaction
    if not is_responsible_for_key(transaction_id):
        logger.debug(f"Node {NODE_ID} is not responsible for transaction {transaction_id}")
        return
    
    logger.info(f"Processing transaction {transaction_id}")
    
    # Get database session
    with get_db() as db:
        # Get transaction from database
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        
        if not transaction:
            logger.error(f"Transaction {transaction_id} not found in database")
            return
        
        if transaction.status != TransactionStatus.PENDING:
            logger.info(f"Transaction {transaction_id} is not in PENDING state (current: {transaction.status})")
            return
        
        # Process transaction
        try:
            # Debit from source account
            debit_success = await update_account_balance(
                transaction.from_account_id,
                transaction.amount,
                True,
                f"Payment: {transaction.reference_id}"
            )
            
            if not debit_success:
                # Failed to debit, mark transaction as failed
                transaction.status = TransactionStatus.FAILED
                db.commit()
                
                # Notify transaction status update
                kafka_client.produce_message(
                    "transaction_events",
                    {
                        "event_type": "transaction_failed",
                        "transaction_id": transaction.id,
                        "reference_id": transaction.reference_id,
                        "reason": "Failed to debit source account"
                    },
                    key=transaction.id
                )
                return
            
            # Credit to destination account
            credit_success = await update_account_balance(
                transaction.to_account_id,
                transaction.amount,
                False,
                f"Payment received: {transaction.reference_id}"
            )
            
            if not credit_success:
                # Failed to credit, should revert the debit and mark as failed
                # In a real system, this would be more complex with a compensation transaction
                await update_account_balance(
                    transaction.from_account_id,
                    transaction.amount,
                    False,
                    f"Reversal: {transaction.reference_id}"
                )
                
                transaction.status = TransactionStatus.FAILED
                db.commit()
                
                # Notify transaction status update
                kafka_client.produce_message(
                    "transaction_events",
                    {
                        "event_type": "transaction_failed",
                        "transaction_id": transaction.id,
                        "reference_id": transaction.reference_id,
                        "reason": "Failed to credit destination account"
                    },
                    key=transaction.id
                )
                return
            
            # Transaction successful
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.utcnow()
            db.commit()
            
            # Notify transaction completed
            kafka_client.produce_message(
                "transaction_events",
                {
                    "event_type": "transaction_completed",
                    "transaction_id": transaction.id,
                    "reference_id": transaction.reference_id,
                    "from_account_id": transaction.from_account_id,
                    "to_account_id": transaction.to_account_id,
                    "amount": transaction.amount,
                    "currency": transaction.currency,
                    "completed_at": transaction.completed_at.isoformat() if transaction.completed_at else None
                },
                key=transaction.id
            )
            
            logger.info(f"Transaction {transaction_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing transaction {transaction_id}: {e}")
            
            # Mark transaction as failed
            transaction.status = TransactionStatus.FAILED
            db.commit()
            
            # Notify transaction status update
            kafka_client.produce_message(
                "transaction_events",
                {
                    "event_type": "transaction_failed",
                    "transaction_id": transaction.id,
                    "reference_id": transaction.reference_id,
                    "reason": str(e)
                },
                key=transaction.id
            )

# Submit transaction to Kafka for processing
async def submit_transaction_to_kafka(transaction: Transaction):
    """
    Submit a transaction to Kafka for processing.
    """
    transaction_dict = {
        "transaction_id": transaction.id,
        "from_account_id": transaction.from_account_id,
        "to_account_id": transaction.to_account_id,
        "amount": transaction.amount,
        "currency": transaction.currency,
        "transaction_type": transaction.transaction_type.value,
        "reference_id": transaction.reference_id,
        "description": transaction.description,
        "submitted_at": datetime.utcnow().isoformat()
    }
    
    # Produce message to Kafka
    kafka_client.produce_message(
        TRANSACTION_TOPIC,
        transaction_dict,
        key=transaction.id
    )
    
    logger.info(f"Transaction {transaction.id} submitted to Kafka for processing")

# Create transaction endpoint
@app.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new transaction.
    """
    # Verify source account ownership
    is_owner = await verify_account_ownership(transaction_data.from_account_id, current_user["id"])
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own the source account"
        )
    
    # Create transaction
    transaction = Transaction(
        from_account_id=transaction_data.from_account_id,
        to_account_id=transaction_data.to_account_id,
        amount=transaction_data.amount,
        currency=transaction_data.currency,
        transaction_type=transaction_data.transaction_type,
        description=transaction_data.description,
        metadata=json.dumps(transaction_data.metadata) if transaction_data.metadata else None,
        node_id=NODE_ID,
        partition_key=transaction_data.from_account_id  # Use source account as partition key for consistent routing
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    # Submit transaction to Kafka for processing in the background
    background_tasks.add_task(submit_transaction_to_kafka, transaction)
    
    return transaction

# Get all transactions for the current user
@app.get("/transactions", response_model=TransactionListResponse)
async def get_user_transactions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    status: Optional[TransactionStatus] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get all transactions for the authenticated user.
    """
    # Get all accounts for the user
    # In a real system, this would be a service call to the account service
    # Here we're querying directly for simplicity
    user_accounts = db.query(Account).filter(Account.user_id == current_user["id"]).all()
    account_ids = [account.id for account in user_accounts]
    
    if not account_ids:
        return {"transactions": [], "total": 0}
    
    # Query transactions
    query = db.query(Transaction).filter(
        or_(
            Transaction.from_account_id.in_(account_ids),
            Transaction.to_account_id.in_(account_ids)
        )
    )
    
    if status:
        query = query.filter(Transaction.status == status)
    
    total = query.count()
    transactions = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
    
    return {"transactions": transactions, "total": total}

# Get transaction by ID
@app.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a transaction by ID.
    """
    # Get all accounts for the user
    user_accounts = db.query(Account).filter(Account.user_id == current_user["id"]).all()
    account_ids = [account.id for account in user_accounts]
    
    if not account_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Query transaction
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        or_(
            Transaction.from_account_id.in_(account_ids),
            Transaction.to_account_id.in_(account_ids)
        )
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
        
    return transaction

# Make a payment (higher-level endpoint)
@app.post("/payments", response_model=TransactionResponse)
async def make_payment(
    payment_data: PaymentRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Make a payment from one account to another.
    """
    # Verify source account ownership
    is_owner = await verify_account_ownership(payment_data.from_account_id, current_user["id"])
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own the source account"
        )
    
    # Create transaction with payment type
    transaction = Transaction(
        from_account_id=payment_data.from_account_id,
        to_account_id=payment_data.to_account_id,
        amount=payment_data.amount,
        currency=payment_data.currency,
        transaction_type=TransactionType.PAYMENT,
        description=payment_data.description,
        metadata=json.dumps(payment_data.metadata) if payment_data.metadata else None,
        node_id=NODE_ID,
        partition_key=payment_data.from_account_id
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    # Submit transaction to Kafka for processing in the background
    background_tasks.add_task(submit_transaction_to_kafka, transaction)
    
    return transaction

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "service": "transaction"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8003"))) 