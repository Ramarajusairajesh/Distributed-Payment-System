from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from app.common.database.db import Base
import uuid
from datetime import datetime
import enum

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"

class TransactionType(str, enum.Enum):
    PAYMENT = "payment"
    TRANSFER = "transfer"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    REFUND = "refund"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Account references
    from_account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    to_account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    
    # Transaction details
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    transaction_type = Column(Enum(TransactionType), default=TransactionType.TRANSFER)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    
    # Transaction tracking
    reference_id = Column(String, unique=True, index=True, default=lambda: f"TXN-{uuid.uuid4().hex[:12].upper()}")
    description = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # For storing JSON data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Distributed system tracking
    node_id = Column(String, nullable=True)  # Which node processed this transaction
    partition_key = Column(String, nullable=True)  # For Kafka partitioning
    
    # Relationships
    from_account = relationship("Account", foreign_keys=[from_account_id], back_populates="transactions_from")
    to_account = relationship("Account", foreign_keys=[to_account_id], back_populates="transactions_to")
    
    def __repr__(self):
        return f"Transaction(id={self.id}, from={self.from_account_id}, to={self.to_account_id}, amount={self.amount}, status={self.status})" 