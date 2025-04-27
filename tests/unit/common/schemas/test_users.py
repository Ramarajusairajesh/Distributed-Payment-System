import pytest
from datetime import datetime
from pydantic import ValidationError

from app.common.schemas.users import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserInDB,
    UserResponse,
    Token,
    TokenPayload
)

class TestUserSchemas:
    """Test cases for user Pydantic schemas."""

    def test_user_base_valid(self):
        """Test valid UserBase creation."""
        # Minimal data
        user = UserBase(username="testuser", email="test@example.com")
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name is None
        
        # With optional fields
        user = UserBase(
            username="testuser",
            email="test@example.com",
            full_name="Test User"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"

    def test_user_base_invalid(self):
        """Test validation errors for UserBase."""
        # Username too short
        with pytest.raises(ValidationError) as exc_info:
            UserBase(username="ab", email="test@example.com")
        assert "username" in str(exc_info.value)
        
        # Username too long
        with pytest.raises(ValidationError) as exc_info:
            UserBase(username="a" * 51, email="test@example.com")
        assert "username" in str(exc_info.value)
        
        # Invalid email
        with pytest.raises(ValidationError) as exc_info:
            UserBase(username="testuser", email="invalid-email")
        assert "email" in str(exc_info.value)

    def test_user_create_valid(self):
        """Test valid UserCreate creation."""
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            password="Password123"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "Password123"

    def test_user_create_password_validation(self):
        """Test password validation in UserCreate."""
        # Password too short
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="Pass1"
            )
        assert "password" in str(exc_info.value)
        
        # Password without uppercase
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="password123"
            )
        assert "Password must contain at least one uppercase letter" in str(exc_info.value)
        
        # Password without lowercase
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="PASSWORD123"
            )
        assert "Password must contain at least one lowercase letter" in str(exc_info.value)
        
        # Password without digit
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="PasswordABC"
            )
        assert "Password must contain at least one digit" in str(exc_info.value)

    def test_user_update_valid(self):
        """Test valid UserUpdate creation."""
        # Empty update is valid
        user_update = UserUpdate()
        assert user_update.username is None
        assert user_update.email is None
        assert user_update.full_name is None
        assert user_update.is_active is None
        
        # Partial update
        user_update = UserUpdate(
            username="newusername",
            is_active=False
        )
        assert user_update.username == "newusername"
        assert user_update.email is None
        assert user_update.is_active is False

    def test_user_update_validation(self):
        """Test validation in UserUpdate."""
        # Username too short
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(username="ab")
        assert "username" in str(exc_info.value)
        
        # Invalid email
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(email="invalid-email")
        assert "email" in str(exc_info.value)

    def test_user_in_db(self):
        """Test UserInDB creation."""
        now = datetime.utcnow()
        user = UserInDB(
            id="user-id",
            username="testuser",
            email="test@example.com",
            is_active=True,
            is_superuser=False,
            created_at=now,
            updated_at=now
        )
        
        assert user.id == "user-id"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.created_at == now
        assert user.updated_at == now

    def test_user_response(self):
        """Test UserResponse creation."""
        now = datetime.utcnow()
        user = UserResponse(
            id="user-id",
            username="testuser",
            email="test@example.com",
            is_active=True,
            is_superuser=False,
            created_at=now,
            updated_at=now
        )
        
        assert user.id == "user-id"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.created_at == now
        assert user.updated_at == now

    def test_token(self):
        """Test Token schema."""
        token = Token(access_token="test-token")
        assert token.access_token == "test-token"
        assert token.token_type == "bearer"
        
        # Custom token type
        token = Token(access_token="test-token", token_type="custom")
        assert token.token_type == "custom"

    def test_token_payload(self):
        """Test TokenPayload schema."""
        # Minimal payload
        payload = TokenPayload(sub="user-id", exp=1234567890)
        assert payload.sub == "user-id"
        assert payload.exp == 1234567890
        assert payload.user_data is None
        
        # With user data
        user_data = {"id": "user-id", "is_admin": True}
        payload = TokenPayload(sub="user-id", exp=1234567890, user_data=user_data)
        assert payload.user_data == user_data 