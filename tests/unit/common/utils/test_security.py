import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.common.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    JWT_SECRET,
    JWT_ALGORITHM
)

class TestSecurity:
    """Test cases for security utilities."""

    def test_password_hashing(self):
        """Test that password hashing and verification works correctly."""
        password = "TestPassword123"
        hashed = get_password_hash(password)
        
        # Verify the hash is different from the original password
        assert hashed != password
        
        # Verify that verification works with correct password
        assert verify_password(password, hashed) is True
        
        # Verify that verification fails with incorrect password
        assert verify_password("WrongPassword", hashed) is False

    def test_create_access_token(self):
        """Test that access token is created correctly."""
        # Test data
        user_id = "test_user"
        expires_delta = timedelta(minutes=30)
        additional_data = {"user_data": {"id": user_id, "is_admin": False}}
        
        # Create token
        token = create_access_token(
            subject=user_id,
            expires_delta=expires_delta,
            additional_data=additional_data
        )
        
        # Verify token is a string
        assert isinstance(token, str)
        
        # Decode token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Verify payload contains expected data
        assert payload["sub"] == user_id
        assert "exp" in payload
        assert payload["user_data"]["id"] == user_id
        assert payload["user_data"]["is_admin"] is False

    def test_decode_access_token(self):
        """Test that access token can be decoded correctly."""
        # Generate a token
        user_id = "test_user"
        exp_time = datetime.utcnow() + timedelta(minutes=30)
        payload = {
            "sub": user_id,
            "exp": exp_time.timestamp(),
            "test_data": "test_value"
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Decode token
        decoded = decode_access_token(token)
        
        # Verify decoded data
        assert decoded["sub"] == user_id
        assert decoded["test_data"] == "test_value"
        assert abs(decoded["exp"] - exp_time.timestamp()) < 1  # Allow for small time differences

    def test_token_expiration(self):
        """Test that expired tokens are rejected."""
        # Generate an expired token
        user_id = "test_user"
        exp_time = datetime.utcnow() - timedelta(minutes=10)  # Expired 10 minutes ago
        payload = {
            "sub": user_id,
            "exp": exp_time.timestamp()
        }
        expired_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Attempt to decode should raise an error
        with pytest.raises(jwt.JWTError):
            decode_access_token(expired_token)

    def test_default_expiration(self):
        """Test that token uses default expiration when not provided."""
        user_id = "test_user"
        
        # Create token without explicit expiration
        token = create_access_token(subject=user_id)
        
        # Decode token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Verify expiration is set
        assert "exp" in payload
        
        # Expiration should be in the future
        exp_time = datetime.fromtimestamp(payload["exp"])
        assert exp_time > datetime.utcnow() 