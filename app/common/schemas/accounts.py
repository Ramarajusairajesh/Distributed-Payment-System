from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re

class AccountType(str, Enum):
    PERSONAL = "personal"
    BUSINESS = "business"
    SAVINGS = "savings"

class AccountStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"

class AccountBase(BaseModel):
    """Base account schema with common attributes."""
    account_type: Optional[AccountType] = AccountType.PERSONAL
    currency: str = Field(default="USD", regex=r"^[A-Z]{3}$")

class AccountCreate(AccountBase):
    """Schema for creating a new account."""
    pass

class AccountUpdate(BaseModel):
    """Schema for updating an account."""
    account_type: Optional[AccountType] = None
    status: Optional[AccountStatus] = None
    currency: Optional[str] = Field(None, regex=r"^[A-Z]{3}$")
    
    class Config:
        orm_mode = True

class AccountInDB(AccountBase):
    """Schema for account data stored in database."""
    id: str
    user_id: str
    account_number: str
    status: AccountStatus
    balance: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class AccountResponse(AccountInDB):
    """Schema for account data returned in API responses."""
    pass

class BalanceUpdate(BaseModel):
    """Schema for updating account balance."""
    amount: float = Field(..., gt=0)
    description: Optional[str] = None

class AccountListResponse(BaseModel):
    """Schema for list of accounts."""
    accounts: List[AccountResponse]
    total: int 