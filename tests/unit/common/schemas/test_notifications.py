import pytest
from datetime import datetime
from pydantic import ValidationError

from app.common.schemas.notifications import (
    NotificationType,
    NotificationPriority,
    NotificationStatus,
    NotificationBase,
    NotificationCreate,
    NotificationUpdate,
    NotificationInDB,
    NotificationResponse,
    NotificationListResponse
)

class TestNotificationSchemas:
    """Test cases for notification Pydantic schemas."""

    def test_notification_type_enum(self):
        """Test NotificationType enum."""
        assert NotificationType.TRANSACTION == "transaction"
        assert NotificationType.SECURITY == "security"
        assert NotificationType.ACCOUNT == "account"
        assert NotificationType.SYSTEM == "system"
        
        # Test conversion from string
        assert NotificationType("transaction") == NotificationType.TRANSACTION
        assert NotificationType("security") == NotificationType.SECURITY
        assert NotificationType("account") == NotificationType.ACCOUNT
        assert NotificationType("system") == NotificationType.SYSTEM
        
        # Test invalid value
        with pytest.raises(ValueError):
            NotificationType("invalid")

    def test_notification_priority_enum(self):
        """Test NotificationPriority enum."""
        assert NotificationPriority.LOW == "low"
        assert NotificationPriority.MEDIUM == "medium"
        assert NotificationPriority.HIGH == "high"
        assert NotificationPriority.CRITICAL == "critical"
        
        # Test conversion from string
        assert NotificationPriority("low") == NotificationPriority.LOW
        assert NotificationPriority("medium") == NotificationPriority.MEDIUM
        assert NotificationPriority("high") == NotificationPriority.HIGH
        assert NotificationPriority("critical") == NotificationPriority.CRITICAL
        
        # Test invalid value
        with pytest.raises(ValueError):
            NotificationPriority("invalid")

    def test_notification_status_enum(self):
        """Test NotificationStatus enum."""
        assert NotificationStatus.PENDING == "pending"
        assert NotificationStatus.SENT == "sent"
        assert NotificationStatus.DELIVERED == "delivered"
        assert NotificationStatus.READ == "read"
        assert NotificationStatus.FAILED == "failed"
        
        # Test conversion from string
        assert NotificationStatus("pending") == NotificationStatus.PENDING
        assert NotificationStatus("sent") == NotificationStatus.SENT
        assert NotificationStatus("delivered") == NotificationStatus.DELIVERED
        assert NotificationStatus("read") == NotificationStatus.READ
        assert NotificationStatus("failed") == NotificationStatus.FAILED
        
        # Test invalid value
        with pytest.raises(ValueError):
            NotificationStatus("invalid")

    def test_notification_base_valid(self):
        """Test valid NotificationBase creation."""
        # Minimal required fields
        notification = NotificationBase(
            user_id="user-123",
            title="Test Notification",
            message="This is a test notification"
        )
        assert notification.user_id == "user-123"
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test notification"
        assert notification.notification_type == NotificationType.SYSTEM  # Default
        assert notification.priority == NotificationPriority.MEDIUM  # Default
        assert notification.data is None
        
        # With all fields
        notification = NotificationBase(
            user_id="user-123",
            title="Transaction Alert",
            message="Your account was credited with $500",
            notification_type=NotificationType.TRANSACTION,
            priority=NotificationPriority.HIGH,
            data={"transaction_id": "txn-123", "amount": 500.00}
        )
        assert notification.user_id == "user-123"
        assert notification.title == "Transaction Alert"
        assert notification.message == "Your account was credited with $500"
        assert notification.notification_type == NotificationType.TRANSACTION
        assert notification.priority == NotificationPriority.HIGH
        assert notification.data == {"transaction_id": "txn-123", "amount": 500.00}

    def test_notification_base_validation(self):
        """Test validation in NotificationBase."""
        # Title too short
        with pytest.raises(ValidationError) as exc_info:
            NotificationBase(
                user_id="user-123",
                title="",  # Empty title
                message="This is a test notification"
            )
        assert "title" in str(exc_info.value)
        
        # Message too short
        with pytest.raises(ValidationError) as exc_info:
            NotificationBase(
                user_id="user-123",
                title="Test Notification",
                message=""  # Empty message
            )
        assert "message" in str(exc_info.value)

    def test_notification_create(self):
        """Test NotificationCreate creation."""
        # Minimal
        notification = NotificationCreate(
            user_id="user-123",
            title="Test Notification",
            message="This is a test notification"
        )
        assert notification.user_id == "user-123"
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test notification"
        assert notification.notification_type == NotificationType.SYSTEM
        assert notification.priority == NotificationPriority.MEDIUM
        
        # Complete
        notification = NotificationCreate(
            user_id="user-123",
            title="Security Alert",
            message="Unusual login detected from a new device",
            notification_type=NotificationType.SECURITY,
            priority=NotificationPriority.CRITICAL,
            data={"ip_address": "192.168.1.1", "location": "Unknown"}
        )
        assert notification.user_id == "user-123"
        assert notification.title == "Security Alert"
        assert notification.message == "Unusual login detected from a new device"
        assert notification.notification_type == NotificationType.SECURITY
        assert notification.priority == NotificationPriority.CRITICAL
        assert notification.data == {"ip_address": "192.168.1.1", "location": "Unknown"}

    def test_notification_update(self):
        """Test NotificationUpdate creation."""
        # Empty update
        update = NotificationUpdate()
        assert update.status is None
        assert update.data is None
        
        # Status update only
        update = NotificationUpdate(
            status=NotificationStatus.DELIVERED
        )
        assert update.status == NotificationStatus.DELIVERED
        assert update.data is None
        
        # Status update with data
        update = NotificationUpdate(
            status=NotificationStatus.READ,
            data={"read_at": "2023-04-01T12:00:00Z"}
        )
        assert update.status == NotificationStatus.READ
        assert update.data == {"read_at": "2023-04-01T12:00:00Z"}

    def test_notification_in_db(self):
        """Test NotificationInDB creation."""
        now = datetime.utcnow()
        notification = NotificationInDB(
            id="notification-123",
            user_id="user-123",
            title="Test Notification",
            message="This is a test notification",
            status=NotificationStatus.PENDING,
            created_at=now,
            updated_at=now
        )
        
        assert notification.id == "notification-123"
        assert notification.user_id == "user-123"
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test notification"
        assert notification.notification_type == NotificationType.SYSTEM  # Default
        assert notification.priority == NotificationPriority.MEDIUM  # Default
        assert notification.status == NotificationStatus.PENDING
        assert notification.data is None
        assert notification.created_at == now
        assert notification.updated_at == now
        
        # Complete notification
        notification = NotificationInDB(
            id="notification-123",
            user_id="user-123",
            title="Transaction Notification",
            message="Your payment of $100 was processed",
            notification_type=NotificationType.TRANSACTION,
            priority=NotificationPriority.HIGH,
            status=NotificationStatus.SENT,
            data={"transaction_id": "txn-456", "amount": 100.00},
            created_at=now,
            updated_at=now
        )
        
        assert notification.id == "notification-123"
        assert notification.user_id == "user-123"
        assert notification.title == "Transaction Notification"
        assert notification.message == "Your payment of $100 was processed"
        assert notification.notification_type == NotificationType.TRANSACTION
        assert notification.priority == NotificationPriority.HIGH
        assert notification.status == NotificationStatus.SENT
        assert notification.data == {"transaction_id": "txn-456", "amount": 100.00}
        assert notification.created_at == now
        assert notification.updated_at == now

    def test_notification_response(self):
        """Test NotificationResponse creation."""
        now = datetime.utcnow()
        notification = NotificationResponse(
            id="notification-123",
            user_id="user-123",
            title="Test Notification",
            message="This is a test notification",
            notification_type=NotificationType.SYSTEM,
            priority=NotificationPriority.MEDIUM,
            status=NotificationStatus.DELIVERED,
            created_at=now,
            updated_at=now
        )
        
        assert notification.id == "notification-123"
        assert notification.user_id == "user-123"
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test notification"
        assert notification.notification_type == NotificationType.SYSTEM
        assert notification.priority == NotificationPriority.MEDIUM
        assert notification.status == NotificationStatus.DELIVERED
        assert notification.data is None
        assert notification.created_at == now
        assert notification.updated_at == now

    def test_notification_list_response(self):
        """Test NotificationListResponse creation."""
        now = datetime.utcnow()
        notification1 = NotificationResponse(
            id="notification-123",
            user_id="user-123",
            title="First Notification",
            message="This is the first notification",
            notification_type=NotificationType.SYSTEM,
            priority=NotificationPriority.LOW,
            status=NotificationStatus.READ,
            created_at=now,
            updated_at=now
        )
        
        notification2 = NotificationResponse(
            id="notification-456",
            user_id="user-123",
            title="Second Notification",
            message="This is the second notification",
            notification_type=NotificationType.ACCOUNT,
            priority=NotificationPriority.HIGH,
            status=NotificationStatus.SENT,
            created_at=now,
            updated_at=now
        )
        
        response = NotificationListResponse(
            notifications=[notification1, notification2],
            total=2
        )
        
        assert len(response.notifications) == 2
        assert response.notifications[0].id == "notification-123"
        assert response.notifications[1].id == "notification-456"
        assert response.total == 2 