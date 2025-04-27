# API Documentation

This document provides details about the Distributed Payment System API endpoints and how to use them.

## Base URL

The base URL for all API endpoints is:

```
http://<host>:8000
```

For local development, the host will be `localhost`.

## Authentication

Most endpoints require authentication using a JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

To get a token, use the `/auth/token` endpoint.

## API Endpoints

### Authentication

#### Login

```
POST /auth/token
```

Request body (form data):
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Register

```
POST /auth/register
```

Request body:
```json
{
  "username": "new_user",
  "email": "user@example.com",
  "password": "SecurePassword123",
  "full_name": "John Doe"
}
```

Response:
```json
{
  "id": "user-uuid",
  "username": "new_user",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2023-08-01T12:00:00.000Z",
  "updated_at": "2023-08-01T12:00:00.000Z"
}
```

#### Get User Info

```
GET /auth/users/me
```

Response:
```json
{
  "id": "user-uuid",
  "username": "your_username",
  "email": "your_email@example.com",
  "full_name": "Your Name",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2023-08-01T12:00:00.000Z",
  "updated_at": "2023-08-01T12:00:00.000Z"
}
```

### Accounts

#### Create Account

```
POST /accounts
```

Request body:
```json
{
  "account_type": "personal",
  "currency": "USD"
}
```

Response:
```json
{
  "id": "account-uuid",
  "user_id": "user-uuid",
  "account_number": "ACC-12345678",
  "account_type": "personal",
  "status": "active",
  "balance": 0.0,
  "currency": "USD",
  "created_at": "2023-08-01T12:00:00.000Z",
  "updated_at": "2023-08-01T12:00:00.000Z"
}
```

#### Get All Accounts

```
GET /accounts
```

Response:
```json
{
  "accounts": [
    {
      "id": "account-uuid",
      "user_id": "user-uuid",
      "account_number": "ACC-12345678",
      "account_type": "personal",
      "status": "active",
      "balance": 0.0,
      "currency": "USD",
      "created_at": "2023-08-01T12:00:00.000Z",
      "updated_at": "2023-08-01T12:00:00.000Z"
    }
  ],
  "total": 1
}
```

#### Get Account Details

```
GET /accounts/{account_id}
```

Response:
```json
{
  "id": "account-uuid",
  "user_id": "user-uuid",
  "account_number": "ACC-12345678",
  "account_type": "personal",
  "status": "active",
  "balance": 0.0,
  "currency": "USD",
  "created_at": "2023-08-01T12:00:00.000Z",
  "updated_at": "2023-08-01T12:00:00.000Z"
}
```

#### Update Account

```
PUT /accounts/{account_id}
```

Request body:
```json
{
  "account_type": "business",
  "status": "active",
  "currency": "EUR"
}
```

Response: Updated account object

#### Deposit Funds

```
POST /accounts/{account_id}/deposit
```

Request body:
```json
{
  "amount": 1000.00,
  "description": "Initial deposit"
}
```

Response: Updated account object with new balance

### Transactions

#### Create Transaction

```
POST /transactions
```

Request body:
```json
{
  "from_account_id": "source-account-uuid",
  "to_account_id": "destination-account-uuid",
  "amount": 50.00,
  "currency": "USD",
  "transaction_type": "transfer",
  "description": "Monthly rent payment",
  "metadata": {
    "category": "housing"
  }
}
```

Response: Created transaction object

#### Make Payment (Simplified)

```
POST /payments
```

Request body:
```json
{
  "from_account_id": "source-account-uuid",
  "to_account_id": "destination-account-uuid",
  "amount": 50.00,
  "currency": "USD",
  "description": "Coffee payment",
  "metadata": {
    "category": "food"
  }
}
```

Response: Created transaction object with payment type

#### Get All Transactions

```
GET /transactions
```

Query parameters:
- `status`: Filter by transaction status (optional)
- `limit`: Maximum number of transactions to return (default: 100)
- `offset`: Offset for pagination (default: 0)

Response:
```json
{
  "transactions": [
    {
      "id": "transaction-uuid",
      "from_account_id": "source-account-uuid",
      "to_account_id": "destination-account-uuid",
      "amount": 50.00,
      "currency": "USD",
      "transaction_type": "payment",
      "status": "completed",
      "reference_id": "TXN-12345ABCDE",
      "description": "Coffee payment",
      "metadata": {
        "category": "food"
      },
      "created_at": "2023-08-01T12:00:00.000Z",
      "updated_at": "2023-08-01T12:01:00.000Z",
      "completed_at": "2023-08-01T12:01:00.000Z",
      "node_id": "node1"
    }
  ],
  "total": 1
}
```

#### Get Transaction Details

```
GET /transactions/{transaction_id}
```

Response: Transaction object

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message"
}
```

Common HTTP status codes:

- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Not enough permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Rate Limiting

API endpoints are rate-limited to 100 requests per minute per IP address. 