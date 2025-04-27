import pytest
from datetime import datetime
from pydantic import ValidationError

from app.common.schemas.audit import (
    AuditActionType,
    AuditResourceType,
    AuditLogBase,
    AuditLogCreate,
    AuditLogInDB,
    AuditLogResponse,
    AuditLogListResponse
)

class TestAuditSchemas:
    """Test cases for audit log Pydantic schemas."""

    def test_audit_action_type_enum(self):
        """Test AuditActionType enum."""
        assert AuditActionType.CREATE == "create"
        assert AuditActionType.READ == "read"
        assert AuditActionType.UPDATE == "update"
        assert AuditActionType.DELETE == "delete"
        assert AuditActionType.LOGIN == "login"
        assert AuditActionType.LOGOUT == "logout"
        assert AuditActionType.FAILED_LOGIN == "failed_login"
        
        # Test conversion from string
        assert AuditActionType("create") == AuditActionType.CREATE
        assert AuditActionType("read") == AuditActionType.READ
        assert AuditActionType("update") == AuditActionType.UPDATE
        assert AuditActionType("delete") == AuditActionType.DELETE
        assert AuditActionType("login") == AuditActionType.LOGIN
        assert AuditActionType("logout") == AuditActionType.LOGOUT
        assert AuditActionType("failed_login") == AuditActionType.FAILED_LOGIN
        
        # Test invalid value
        with pytest.raises(ValueError):
            AuditActionType("invalid")

    def test_audit_resource_type_enum(self):
        """Test AuditResourceType enum."""
        assert AuditResourceType.USER == "user"
        assert AuditResourceType.ACCOUNT == "account"
        assert AuditResourceType.TRANSACTION == "transaction"
        assert AuditResourceType.NOTIFICATION == "notification"
        assert AuditResourceType.SYSTEM == "system"
        
        # Test conversion from string
        assert AuditResourceType("user") == AuditResourceType.USER
        assert AuditResourceType("account") == AuditResourceType.ACCOUNT
        assert AuditResourceType("transaction") == AuditResourceType.TRANSACTION
        assert AuditResourceType("notification") == AuditResourceType.NOTIFICATION
        assert AuditResourceType("system") == AuditResourceType.SYSTEM
        
        # Test invalid value
        with pytest.raises(ValueError):
            AuditResourceType("invalid")

    def test_audit_log_base_valid(self):
        """Test valid AuditLogBase creation."""
        # Minimal
        audit_log = AuditLogBase(
            user_id="user-123",
            action=AuditActionType.CREATE,
            resource_type=AuditResourceType.ACCOUNT,
            ip_address="192.168.1.1"
        )
        assert audit_log.user_id == "user-123"
        assert audit_log.action == AuditActionType.CREATE
        assert audit_log.resource_type == AuditResourceType.ACCOUNT
        assert audit_log.ip_address == "192.168.1.1"
        assert audit_log.resource_id is None
        assert audit_log.details is None
        
        # With all fields
        audit_log = AuditLogBase(
            user_id="user-123",
            action=AuditActionType.UPDATE,
            resource_type=AuditResourceType.ACCOUNT,
            resource_id="account-456",
            ip_address="192.168.1.1",
            details={"balance_before": 1000, "balance_after": 1500}
        )
        assert audit_log.user_id == "user-123"
        assert audit_log.action == AuditActionType.UPDATE
        assert audit_log.resource_type == AuditResourceType.ACCOUNT
        assert audit_log.resource_id == "account-456"
        assert audit_log.ip_address == "192.168.1.1"
        assert audit_log.details == {"balance_before": 1000, "balance_after": 1500}

    def test_audit_log_base_ip_validation(self):
        """Test IP address validation in AuditLogBase."""
        # Valid IP addresses
        AuditLogBase(
            user_id="user-123",
            action=AuditActionType.CREATE,
            resource_type=AuditResourceType.ACCOUNT,
            ip_address="192.168.1.1"
        )
        
        AuditLogBase(
            user_id="user-123",
            action=AuditActionType.CREATE,
            resource_type=AuditResourceType.ACCOUNT,
            ip_address="2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        )
        
        # Invalid IP
        with pytest.raises(ValidationError) as exc_info:
            AuditLogBase(
                user_id="user-123",
                action=AuditActionType.CREATE,
                resource_type=AuditResourceType.ACCOUNT,
                ip_address="invalid-ip"
            )
        assert "ip_address" in str(exc_info.value)

    def test_audit_log_create(self):
        """Test AuditLogCreate creation."""
        # Basic creation
        audit_log = AuditLogCreate(
            user_id="user-123",
            action=AuditActionType.READ,
            resource_type=AuditResourceType.TRANSACTION,
            ip_address="192.168.1.1"
        )
        assert audit_log.user_id == "user-123"
        assert audit_log.action == AuditActionType.READ
        assert audit_log.resource_type == AuditResourceType.TRANSACTION
        assert audit_log.ip_address == "192.168.1.1"
        
        # With resource_id and details
        audit_log = AuditLogCreate(
            user_id="user-123",
            action=AuditActionType.DELETE,
            resource_type=AuditResourceType.NOTIFICATION,
            resource_id="notification-123",
            ip_address="192.168.1.1",
            details={"reason": "User requested deletion"}
        )
        assert audit_log.user_id == "user-123"
        assert audit_log.action == AuditActionType.DELETE
        assert audit_log.resource_type == AuditResourceType.NOTIFICATION
        assert audit_log.resource_id == "notification-123"
        assert audit_log.ip_address == "192.168.1.1"
        assert audit_log.details == {"reason": "User requested deletion"}

    def test_audit_log_in_db(self):
        """Test AuditLogInDB creation."""
        now = datetime.utcnow()
        audit_log = AuditLogInDB(
            id="audit-123",
            user_id="user-123",
            action=AuditActionType.LOGIN,
            resource_type=AuditResourceType.USER,
            ip_address="192.168.1.1",
            created_at=now
        )
        
        assert audit_log.id == "audit-123"
        assert audit_log.user_id == "user-123"
        assert audit_log.action == AuditActionType.LOGIN
        assert audit_log.resource_type == AuditResourceType.USER
        assert audit_log.ip_address == "192.168.1.1"
        assert audit_log.created_at == now
        assert audit_log.resource_id is None
        assert audit_log.details is None
        
        # Complete log
        audit_log = AuditLogInDB(
            id="audit-123",
            user_id="user-123",
            action=AuditActionType.CREATE,
            resource_type=AuditResourceType.TRANSACTION,
            resource_id="txn-456",
            ip_address="192.168.1.1",
            details={"amount": 500, "currency": "USD"},
            created_at=now
        )
        
        assert audit_log.id == "audit-123"
        assert audit_log.user_id == "user-123"
        assert audit_log.action == AuditActionType.CREATE
        assert audit_log.resource_type == AuditResourceType.TRANSACTION
        assert audit_log.resource_id == "txn-456"
        assert audit_log.ip_address == "192.168.1.1"
        assert audit_log.details == {"amount": 500, "currency": "USD"}
        assert audit_log.created_at == now

    def test_audit_log_response(self):
        """Test AuditLogResponse creation."""
        now = datetime.utcnow()
        audit_log = AuditLogResponse(
            id="audit-123",
            user_id="user-123",
            action=AuditActionType.UPDATE,
            resource_type=AuditResourceType.ACCOUNT,
            resource_id="account-456",
            ip_address="192.168.1.1",
            details={"field": "status", "old": "active", "new": "suspended"},
            created_at=now
        )
        
        assert audit_log.id == "audit-123"
        assert audit_log.user_id == "user-123"
        assert audit_log.action == AuditActionType.UPDATE
        assert audit_log.resource_type == AuditResourceType.ACCOUNT
        assert audit_log.resource_id == "account-456"
        assert audit_log.ip_address == "192.168.1.1"
        assert audit_log.details == {"field": "status", "old": "active", "new": "suspended"}
        assert audit_log.created_at == now

    def test_audit_log_list_response(self):
        """Test AuditLogListResponse creation."""
        now = datetime.utcnow()
        log1 = AuditLogResponse(
            id="audit-123",
            user_id="user-123",
            action=AuditActionType.LOGIN,
            resource_type=AuditResourceType.USER,
            ip_address="192.168.1.1",
            created_at=now
        )
        
        log2 = AuditLogResponse(
            id="audit-456",
            user_id="user-123",
            action=AuditActionType.CREATE,
            resource_type=AuditResourceType.ACCOUNT,
            resource_id="account-789",
            ip_address="192.168.1.1",
            created_at=now
        )
        
        response = AuditLogListResponse(
            logs=[log1, log2],
            total=2
        )
        
        assert len(response.logs) == 2
        assert response.logs[0].id == "audit-123"
        assert response.logs[1].id == "audit-456"
        assert response.total == 2

    def test_system_action_without_user(self):
        """Test system action that doesn't require a user."""
        # System action without user ID
        audit_log = AuditLogBase(
            action=AuditActionType.CREATE,
            resource_type=AuditResourceType.SYSTEM,
            ip_address="0.0.0.0",
            details={"event": "System startup"}
        )
        
        assert audit_log.user_id is None
        assert audit_log.action == AuditActionType.CREATE
        assert audit_log.resource_type == AuditResourceType.SYSTEM
        assert audit_log.ip_address == "0.0.0.0"
        assert audit_log.details == {"event": "System startup"} 