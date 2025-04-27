import pytest
from datetime import datetime
from pydantic import ValidationError

from app.common.schemas.transactions import (
    TransactionType,
    TransactionStatus,
    TransactionBase,
    TransactionCreate,
    TransactionUpdate,
    TransactionInDB,
    TransactionResponse,
    TransactionListResponse
)

class TestTransactionSchemas:
    """Test cases for transaction Pydantic schemas."""

    def test_transaction_type_enum(self):
        """Test TransactionType enum."""
        assert TransactionType.DEPOSIT == "deposit"
        assert TransactionType.WITHDRAWAL == "withdrawal"
        assert TransactionType.TRANSFER == "transfer"
        assert TransactionType.PAYMENT == "payment"
        
        # Test conversion from string
        assert TransactionType("deposit") == TransactionType.DEPOSIT
        assert TransactionType("withdrawal") == TransactionType.WITHDRAWAL
        assert TransactionType("transfer") == TransactionType.TRANSFER
        assert TransactionType("payment") == TransactionType.PAYMENT
        
        # Test invalid value
        with pytest.raises(ValueError):
            TransactionType("invalid")

    def test_transaction_status_enum(self):
        """Test TransactionStatus enum."""
        assert TransactionStatus.PENDING == "pending"
        assert TransactionStatus.COMPLETED == "completed"
        assert TransactionStatus.FAILED == "failed"
        assert TransactionStatus.CANCELLED == "cancelled"
        
        # Test conversion from string
        assert TransactionStatus("pending") == TransactionStatus.PENDING
        assert TransactionStatus("completed") == TransactionStatus.COMPLETED
        assert TransactionStatus("failed") == TransactionStatus.FAILED
        assert TransactionStatus("cancelled") == TransactionStatus.CANCELLED
        
        # Test invalid value
        with pytest.raises(ValueError):
            TransactionStatus("invalid")

    def test_transaction_base_valid(self):
        """Test valid TransactionBase creation."""
        # Minimal
        transaction = TransactionBase(
            account_id="account-123",
            amount=100.50,
            transaction_type=TransactionType.DEPOSIT
        )
        assert transaction.account_id == "account-123"
        assert transaction.amount == 100.50
        assert transaction.transaction_type == TransactionType.DEPOSIT
        assert transaction.description is None
        assert transaction.recipient_id is None
        assert transaction.recipient_account_id is None
        
        # Full object
        transaction = TransactionBase(
            account_id="account-123",
            amount=100.50,
            transaction_type=TransactionType.TRANSFER,
            description="Test transfer",
            recipient_id="user-456",
            recipient_account_id="account-456"
        )
        assert transaction.account_id == "account-123"
        assert transaction.amount == 100.50
        assert transaction.transaction_type == TransactionType.TRANSFER
        assert transaction.description == "Test transfer"
        assert transaction.recipient_id == "user-456"
        assert transaction.recipient_account_id == "account-456"

    def test_transaction_base_validation(self):
        """Test validation in TransactionBase."""
        # Amount must be positive
        with pytest.raises(ValidationError) as exc_info:
            TransactionBase(
                account_id="account-123",
                amount=0,
                transaction_type=TransactionType.DEPOSIT
            )
        assert "amount" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            TransactionBase(
                account_id="account-123",
                amount=-100,
                transaction_type=TransactionType.DEPOSIT
            )
        assert "amount" in str(exc_info.value)
        
        # Transfer requires recipient account
        with pytest.raises(ValidationError) as exc_info:
            TransactionBase(
                account_id="account-123",
                amount=100,
                transaction_type=TransactionType.TRANSFER
            )
        assert "recipient_account_id" in str(exc_info.value)

    def test_transaction_create(self):
        """Test TransactionCreate creation."""
        # Simple deposit
        transaction = TransactionCreate(
            account_id="account-123",
            amount=100.50,
            transaction_type=TransactionType.DEPOSIT
        )
        assert transaction.account_id == "account-123"
        assert transaction.amount == 100.50
        assert transaction.transaction_type == TransactionType.DEPOSIT
        
        # Transfer with required fields
        transaction = TransactionCreate(
            account_id="account-123",
            amount=100.50,
            transaction_type=TransactionType.TRANSFER,
            recipient_account_id="account-456"
        )
        assert transaction.account_id == "account-123"
        assert transaction.amount == 100.50
        assert transaction.transaction_type == TransactionType.TRANSFER
        assert transaction.recipient_account_id == "account-456"

    def test_transaction_update(self):
        """Test TransactionUpdate creation."""
        # Status update
        update = TransactionUpdate(
            status=TransactionStatus.COMPLETED
        )
        assert update.status == TransactionStatus.COMPLETED
        assert update.metadata is None
        
        # Status update with metadata
        update = TransactionUpdate(
            status=TransactionStatus.FAILED,
            metadata={"error": "Insufficient funds"}
        )
        assert update.status == TransactionStatus.FAILED
        assert update.metadata == {"error": "Insufficient funds"}

    def test_transaction_in_db(self):
        """Test TransactionInDB creation."""
        now = datetime.utcnow()
        transaction = TransactionInDB(
            id="txn-123",
            account_id="account-123",
            amount=100.50,
            transaction_type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED,
            created_at=now,
            updated_at=now
        )
        
        assert transaction.id == "txn-123"
        assert transaction.account_id == "account-123"
        assert transaction.amount == 100.50
        assert transaction.transaction_type == TransactionType.DEPOSIT
        assert transaction.status == TransactionStatus.COMPLETED
        assert transaction.created_at == now
        assert transaction.updated_at == now
        assert transaction.description is None
        assert transaction.recipient_id is None
        assert transaction.recipient_account_id is None
        assert transaction.metadata == {}
        
        # Transfer transaction
        transaction = TransactionInDB(
            id="txn-123",
            account_id="account-123",
            amount=100.50,
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            recipient_id="user-456",
            recipient_account_id="account-456",
            description="Test transfer",
            metadata={"confirmation_code": "ABC123"},
            created_at=now,
            updated_at=now
        )
        
        assert transaction.id == "txn-123"
        assert transaction.account_id == "account-123"
        assert transaction.amount == 100.50
        assert transaction.transaction_type == TransactionType.TRANSFER
        assert transaction.status == TransactionStatus.COMPLETED
        assert transaction.recipient_id == "user-456"
        assert transaction.recipient_account_id == "account-456"
        assert transaction.description == "Test transfer"
        assert transaction.metadata == {"confirmation_code": "ABC123"}
        assert transaction.created_at == now
        assert transaction.updated_at == now

    def test_transaction_response(self):
        """Test TransactionResponse creation."""
        now = datetime.utcnow()
        transaction = TransactionResponse(
            id="txn-123",
            account_id="account-123",
            amount=100.50,
            transaction_type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED,
            created_at=now,
            updated_at=now
        )
        
        assert transaction.id == "txn-123"
        assert transaction.account_id == "account-123"
        assert transaction.amount == 100.50
        assert transaction.transaction_type == TransactionType.DEPOSIT
        assert transaction.status == TransactionStatus.COMPLETED
        assert transaction.created_at == now
        assert transaction.updated_at == now
        
        # Transfer response
        transaction = TransactionResponse(
            id="txn-123",
            account_id="account-123",
            amount=100.50,
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            recipient_id="user-456",
            recipient_account_id="account-456",
            description="Test transfer",
            created_at=now,
            updated_at=now
        )
        
        assert transaction.id == "txn-123"
        assert transaction.account_id == "account-123"
        assert transaction.amount == 100.50
        assert transaction.transaction_type == TransactionType.TRANSFER
        assert transaction.status == TransactionStatus.COMPLETED
        assert transaction.recipient_id == "user-456"
        assert transaction.recipient_account_id == "account-456"
        assert transaction.description == "Test transfer"
        assert transaction.created_at == now
        assert transaction.updated_at == now

    def test_transaction_list_response(self):
        """Test TransactionListResponse creation."""
        now = datetime.utcnow()
        transaction1 = TransactionResponse(
            id="txn-123",
            account_id="account-123",
            amount=100.50,
            transaction_type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED,
            created_at=now,
            updated_at=now
        )
        
        transaction2 = TransactionResponse(
            id="txn-456",
            account_id="account-123",
            amount=50.25,
            transaction_type=TransactionType.WITHDRAWAL,
            status=TransactionStatus.COMPLETED,
            created_at=now,
            updated_at=now
        )
        
        response = TransactionListResponse(
            transactions=[transaction1, transaction2],
            total=2
        )
        
        assert len(response.transactions) == 2
        assert response.transactions[0].id == "txn-123"
        assert response.transactions[1].id == "txn-456"
        assert response.total == 2 