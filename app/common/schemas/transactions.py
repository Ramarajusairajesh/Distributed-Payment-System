from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import json

class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"

class TransactionType(str, Enum):
    PAYMENT = "payment"
    TRANSFER = "transfer"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    REFUND = "refund"

class TransactionBase(BaseModel):
    """Base transaction schema with common attributes."""
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", regex=r"^[A-Z]{3}$")
    transaction_type: TransactionType = TransactionType.TRANSFER
    description: Optional[str] = None
    transaction_metadata: Optional[Dict[str, Any]] = None

class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    from_account_id: str
    to_account_id: str

class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    status: Optional[TransactionStatus] = None
    description: Optional[str] = None
    transaction_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True

class TransactionInDB(TransactionBase):
    """Schema for transaction data stored in database."""
    id: str
    from_account_id: str
    to_account_id: str
    status: TransactionStatus
    reference_id: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    node_id: Optional[str] = None
    partition_key: Optional[str] = None
    
    class Config:
        orm_mode = True
        
    @validator('transaction_metadata', pre=True)
    def parse_metadata(cls, v):
        """Parse transaction_metadata JSON if it's a string."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return {}
        return v

class TransactionResponse(TransactionInDB):
    """Schema for transaction data returned in API responses."""
    pass

class TransactionListResponse(BaseModel):
    """Schema for list of transactions."""
    transactions: List[TransactionResponse]
    total: int

class PaymentRequest(BaseModel):
    """Schema for a payment request."""
    from_account_id: str
    to_account_id: str
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", regex=r"^[A-Z]{3}$")
    description: Optional[str] = None
    transaction_metadata: Optional[Dict[str, Any]] = None 