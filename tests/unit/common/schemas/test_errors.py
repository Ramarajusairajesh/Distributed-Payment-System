import pytest
from pydantic import ValidationError

from app.common.schemas.errors import (
    ErrorCode,
    ErrorDetail,
    ErrorResponse
)

class TestErrorSchemas:
    """Test cases for error handling Pydantic schemas."""

    def test_error_code_enum(self):
        """Test ErrorCode enum."""
        assert ErrorCode.BAD_REQUEST == "bad_request"
        assert ErrorCode.UNAUTHORIZED == "unauthorized"
        assert ErrorCode.FORBIDDEN == "forbidden"
        assert ErrorCode.NOT_FOUND == "not_found"
        assert ErrorCode.CONFLICT == "conflict"
        assert ErrorCode.UNPROCESSABLE_ENTITY == "unprocessable_entity"
        assert ErrorCode.INTERNAL_SERVER_ERROR == "internal_server_error"
        assert ErrorCode.SERVICE_UNAVAILABLE == "service_unavailable"
        
        # Test conversion from string
        assert ErrorCode("bad_request") == ErrorCode.BAD_REQUEST
        assert ErrorCode("unauthorized") == ErrorCode.UNAUTHORIZED
        assert ErrorCode("forbidden") == ErrorCode.FORBIDDEN
        assert ErrorCode("not_found") == ErrorCode.NOT_FOUND
        assert ErrorCode("conflict") == ErrorCode.CONFLICT
        assert ErrorCode("unprocessable_entity") == ErrorCode.UNPROCESSABLE_ENTITY
        assert ErrorCode("internal_server_error") == ErrorCode.INTERNAL_SERVER_ERROR
        assert ErrorCode("service_unavailable") == ErrorCode.SERVICE_UNAVAILABLE
        
        # Test invalid value
        with pytest.raises(ValueError):
            ErrorCode("invalid")

    def test_error_detail(self):
        """Test ErrorDetail creation."""
        # Basic error detail
        detail = ErrorDetail(
            field="username",
            message="Username already exists"
        )
        assert detail.field == "username"
        assert detail.message == "Username already exists"
        assert detail.code == ErrorCode.BAD_REQUEST  # Default
        
        # Error detail with custom code
        detail = ErrorDetail(
            field="account_id",
            message="Account not found",
            code=ErrorCode.NOT_FOUND
        )
        assert detail.field == "account_id"
        assert detail.message == "Account not found"
        assert detail.code == ErrorCode.NOT_FOUND

    def test_error_detail_validation(self):
        """Test validation in ErrorDetail."""
        # Message required
        with pytest.raises(ValidationError) as exc_info:
            ErrorDetail(field="username", message="")
        assert "message" in str(exc_info.value)

    def test_error_response_basic(self):
        """Test basic ErrorResponse creation."""
        # Simple error response
        response = ErrorResponse(
            message="An error occurred",
            code=ErrorCode.INTERNAL_SERVER_ERROR
        )
        assert response.message == "An error occurred"
        assert response.code == ErrorCode.INTERNAL_SERVER_ERROR
        assert response.details == []
        assert response.request_id is not None  # Auto-generated
        assert response.timestamp is not None  # Auto-generated

    def test_error_response_with_details(self):
        """Test ErrorResponse with details."""
        # Create details
        detail1 = ErrorDetail(
            field="username",
            message="Username is required"
        )
        detail2 = ErrorDetail(
            field="password",
            message="Password must be at least 8 characters",
            code=ErrorCode.UNPROCESSABLE_ENTITY
        )
        
        # Create response with details
        response = ErrorResponse(
            message="Validation error",
            code=ErrorCode.BAD_REQUEST,
            details=[detail1, detail2]
        )
        
        assert response.message == "Validation error"
        assert response.code == ErrorCode.BAD_REQUEST
        assert len(response.details) == 2
        assert response.details[0].field == "username"
        assert response.details[1].field == "password"
        assert response.details[1].code == ErrorCode.UNPROCESSABLE_ENTITY

    def test_error_response_with_request_id(self):
        """Test ErrorResponse with custom request_id."""
        # Create response with custom request_id
        custom_request_id = "req-123456"
        response = ErrorResponse(
            message="Resource not found",
            code=ErrorCode.NOT_FOUND,
            request_id=custom_request_id
        )
        
        assert response.message == "Resource not found"
        assert response.code == ErrorCode.NOT_FOUND
        assert response.request_id == custom_request_id

    def test_error_response_dict_conversion(self):
        """Test ErrorResponse conversion to dict."""
        # Create response
        response = ErrorResponse(
            message="Invalid input",
            code=ErrorCode.BAD_REQUEST,
            details=[
                ErrorDetail(field="email", message="Invalid email format")
            ]
        )
        
        # Convert to dict
        response_dict = response.dict()
        
        # Verify dict contents
        assert response_dict["message"] == "Invalid input"
        assert response_dict["code"] == ErrorCode.BAD_REQUEST
        assert len(response_dict["details"]) == 1
        assert response_dict["details"][0]["field"] == "email"
        assert response_dict["details"][0]["message"] == "Invalid email format"
        assert "request_id" in response_dict
        assert "timestamp" in response_dict 