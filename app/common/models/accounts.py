from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.common.database.db import Base
import uuid
from datetime import datetime
import enum

class AccountType(str, enum.Enum):
    PERSONAL = "personal"
    BUSINESS = "business"
    SAVINGS = "savings"

class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"

class Account(Base):
    __tablename__ = "accounts"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    account_number = Column(String, unique=True, index=True)
    account_type = Column(Enum(AccountType), default=AccountType.PERSONAL)
    status = Column(Enum(AccountStatus), default=AccountStatus.ACTIVE)
    balance = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions_from = relationship("Transaction", foreign_keys="Transaction.from_account_id", back_populates="from_account")
    transactions_to = relationship("Transaction", foreign_keys="Transaction.to_account_id", back_populates="to_account")
    
    def __repr__(self):
        return f"Account(id={self.id}, user_id={self.user_id}, account_number={self.account_number}, balance={self.balance})" 