# Testing Documentation

## Overview

This document describes the testing approach for the Distributed Payment System. The system employs a comprehensive testing strategy across multiple levels to ensure reliability, correctness, and robustness.

## Test Types

### Unit Tests

Unit tests focus on testing individual components in isolation, ensuring each component functions as expected.

#### Schema Tests

Schema tests validate all Pydantic data models used throughout the system:

1. **Account Schemas** (`tests/unit/common/schemas/test_accounts.py`)
   - Tests for `AccountType` and `AccountStatus` enumerations
   - Validation of `AccountBase` fields including currency format
   - Tests for `AccountCreate`, `AccountUpdate`, `AccountInDB`, and `AccountResponse` models
   - Tests for `BalanceUpdate` validation
   - Tests for `AccountListResponse` aggregation

2. **Transaction Schemas** (`tests/unit/common/schemas/test_transactions.py`)
   - Tests for `TransactionType` and `TransactionStatus` enumerations
   - Validation tests for `TransactionBase` (amount must be positive, transfers require recipient)
   - Tests for `TransactionCreate` and `TransactionUpdate` models
   - Tests for `TransactionInDB` and `TransactionResponse` with all attributes
   - Tests for `TransactionListResponse` aggregation

3. **User Schemas** (`tests/unit/common/schemas/test_users.py`)
   - Tests for user creation, validation, and password policy enforcement
   - Tests for JWT token handling
   - Tests for update operations and response formats

4. **Notification Schemas** (`tests/unit/common/schemas/test_notifications.py`)
   - Tests for `NotificationType`, `NotificationPriority`, and `NotificationStatus` enumerations
   - Validation of required fields like title and message
   - Tests for different notification states and update operations
   - Tests for notification listing and aggregation

5. **Error Handling Schemas** (`tests/unit/common/schemas/test_errors.py`)
   - Tests for `ErrorCode` enumeration
   - Tests for `ErrorDetail` creation and validation
   - Tests for `ErrorResponse` with various configurations
   - Tests for dictionary conversion and format consistency

6. **Pagination Schemas** (`tests/unit/common/schemas/test_pagination.py`)
   - Tests for `SortOrder` enumeration
   - Tests for `PaginationParams` with default and custom values
   - Validation of page and limit parameters
   - Tests for offset calculation logic
   - Tests for `PaginatedResponse` with different data types
   - Tests for page calculation and has_more property

7. **Audit Log Schemas** (`tests/unit/common/schemas/test_audit.py`)
   - Tests for `AuditActionType` and `AuditResourceType` enumerations
   - IP address validation tests
   - Tests for different audit log creation scenarios
   - Tests for system actions without a user

### Utility Tests

Tests for core utilities that power the distributed aspects of the system:

1. **Security Utilities** (`tests/unit/common/utils/test_security.py`)
   - Tests for password hashing and verification
   - Tests for JWT token creation and validation
   - Tests for token expiration and claims validation

2. **Distributed Utilities** (`tests/unit/common/utils/test_distributed.py`)
   - Tests for consistent hashing implementation
   - Tests for distributed lock mechanism
   - Tests for node assignment and responsibility calculation

3. **Kafka Messaging** (`tests/unit/common/utils/test_kafka_client.py`)
   - Tests for message production and consumption
   - Tests for metadata handling
   - Tests for client initialization and cleanup

## Running Tests

Tests can be run using pytest with the following commands:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=app

# Run specific test module
pytest tests/unit/common/schemas/test_transactions.py

# Run tests for a specific component
pytest tests/unit/common/schemas/
```

## Test Organization

Tests are organized in a directory structure that mirrors the application code:

```
tests/
├── unit/                  # Unit tests
│   ├── common/            # Common module tests
│   │   ├── schemas/       # Schema tests
│   │   └── utils/         # Utility tests
│   ├── services/          # Service-specific tests
│   └── api/               # API endpoint tests
├── integration/           # Integration tests
└── e2e/                   # End-to-end tests
```

## Continuous Integration

All tests are run as part of the CI/CD pipeline, ensuring that code changes don't break existing functionality. 