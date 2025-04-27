import pytest
from datetime import datetime
from pydantic import ValidationError

from app.common.schemas.accounts import (
    AccountType,
    AccountStatus,
    AccountBase,
    AccountCreate,
    AccountUpdate,
    AccountInDB,
    AccountResponse,
    BalanceUpdate,
    AccountListResponse
)

class TestAccountSchemas:
    """Test cases for account Pydantic schemas."""

    def test_account_type_enum(self):
        """Test AccountType enum."""
        assert AccountType.PERSONAL == "personal"
        assert AccountType.BUSINESS == "business"
        assert AccountType.SAVINGS == "savings"
        
        # Test conversion from string
        assert AccountType("personal") == AccountType.PERSONAL
        assert AccountType("business") == AccountType.BUSINESS
        assert AccountType("savings") == AccountType.SAVINGS
        
        # Test invalid value
        with pytest.raises(ValueError):
            AccountType("invalid")

    def test_account_status_enum(self):
        """Test AccountStatus enum."""
        assert AccountStatus.ACTIVE == "active"
        assert AccountStatus.SUSPENDED == "suspended"
        assert AccountStatus.CLOSED == "closed"
        
        # Test conversion from string
        assert AccountStatus("active") == AccountStatus.ACTIVE
        assert AccountStatus("suspended") == AccountStatus.SUSPENDED
        assert AccountStatus("closed") == AccountStatus.CLOSED
        
        # Test invalid value
        with pytest.raises(ValueError):
            AccountStatus("invalid")

    def test_account_base_valid(self):
        """Test valid AccountBase creation."""
        # Default values
        account = AccountBase()
        assert account.account_type == AccountType.PERSONAL
        assert account.currency == "USD"
        
        # Custom values
        account = AccountBase(
            account_type=AccountType.BUSINESS,
            currency="EUR"
        )
        assert account.account_type == AccountType.BUSINESS
        assert account.currency == "EUR"

    def test_account_base_currency_validation(self):
        """Test currency validation in AccountBase."""
        # Valid 3-letter code
        AccountBase(currency="EUR")
        AccountBase(currency="JPY")
        
        # Invalid currency codes
        with pytest.raises(ValidationError) as exc_info:
            AccountBase(currency="EU")  # Too short
        assert "currency" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            AccountBase(currency="EURO")  # Too long
        assert "currency" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            AccountBase(currency="eur")  # Lowercase
        assert "currency" in str(exc_info.value)

    def test_account_create(self):
        """Test AccountCreate creation."""
        # Default values
        account = AccountCreate()
        assert account.account_type == AccountType.PERSONAL
        assert account.currency == "USD"
        
        # Custom values
        account = AccountCreate(
            account_type=AccountType.BUSINESS,
            currency="EUR"
        )
        assert account.account_type == AccountType.BUSINESS
        assert account.currency == "EUR"

    def test_account_update_valid(self):
        """Test valid AccountUpdate creation."""
        # Empty update
        update = AccountUpdate()
        assert update.account_type is None
        assert update.status is None
        assert update.currency is None
        
        # Partial update
        update = AccountUpdate(
            account_type=AccountType.SAVINGS,
            status=AccountStatus.SUSPENDED
        )
        assert update.account_type == AccountType.SAVINGS
        assert update.status == AccountStatus.SUSPENDED
        assert update.currency is None
        
        # Another partial update
        update = AccountUpdate(currency="EUR")
        assert update.account_type is None
        assert update.status is None
        assert update.currency == "EUR"

    def test_account_update_validation(self):
        """Test validation in AccountUpdate."""
        # Invalid currency
        with pytest.raises(ValidationError) as exc_info:
            AccountUpdate(currency="euro")
        assert "currency" in str(exc_info.value)

    def test_account_in_db(self):
        """Test AccountInDB creation."""
        now = datetime.utcnow()
        account = AccountInDB(
            id="account-id",
            user_id="user-id",
            account_number="ACC-12345",
            status=AccountStatus.ACTIVE,
            balance=1000.50,
            created_at=now,
            updated_at=now
        )
        
        assert account.id == "account-id"
        assert account.user_id == "user-id"
        assert account.account_number == "ACC-12345"
        assert account.status == AccountStatus.ACTIVE
        assert account.account_type == AccountType.PERSONAL  # Default
        assert account.balance == 1000.50
        assert account.currency == "USD"  # Default
        assert account.created_at == now
        assert account.updated_at == now

    def test_account_response(self):
        """Test AccountResponse creation."""
        now = datetime.utcnow()
        account = AccountResponse(
            id="account-id",
            user_id="user-id",
            account_number="ACC-12345",
            account_type=AccountType.BUSINESS,
            status=AccountStatus.ACTIVE,
            balance=1000.50,
            currency="EUR",
            created_at=now,
            updated_at=now
        )
        
        assert account.id == "account-id"
        assert account.user_id == "user-id"
        assert account.account_number == "ACC-12345"
        assert account.account_type == AccountType.BUSINESS
        assert account.status == AccountStatus.ACTIVE
        assert account.balance == 1000.50
        assert account.currency == "EUR"
        assert account.created_at == now
        assert account.updated_at == now

    def test_balance_update_valid(self):
        """Test valid BalanceUpdate creation."""
        # Minimal
        update = BalanceUpdate(amount=100.0)
        assert update.amount == 100.0
        assert update.description is None
        
        # With description
        update = BalanceUpdate(amount=100.0, description="Test deposit")
        assert update.amount == 100.0
        assert update.description == "Test deposit"

    def test_balance_update_validation(self):
        """Test validation in BalanceUpdate."""
        # Amount must be positive
        with pytest.raises(ValidationError) as exc_info:
            BalanceUpdate(amount=0)
        assert "amount" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            BalanceUpdate(amount=-100)
        assert "amount" in str(exc_info.value)

    def test_account_list_response(self):
        """Test AccountListResponse creation."""
        now = datetime.utcnow()
        account1 = AccountResponse(
            id="account-id-1",
            user_id="user-id",
            account_number="ACC-12345",
            status=AccountStatus.ACTIVE,
            balance=1000.50,
            created_at=now,
            updated_at=now
        )
        
        account2 = AccountResponse(
            id="account-id-2",
            user_id="user-id",
            account_number="ACC-67890",
            status=AccountStatus.ACTIVE,
            balance=2000.75,
            created_at=now,
            updated_at=now
        )
        
        response = AccountListResponse(
            accounts=[account1, account2],
            total=2
        )
        
        assert len(response.accounts) == 2
        assert response.accounts[0].id == "account-id-1"
        assert response.accounts[1].id == "account-id-2"
        assert response.total == 2 