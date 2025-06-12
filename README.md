# Distributed Payment System

## Overview
This project implements a distributed payment system that allows for secure and fault-tolerant payment processing across multiple nodes. The system is designed to handle high transaction volumes while maintaining consistency and availability.

## Features
- Distributed transaction processing
- Fault tolerance with replication
- Consistent hashing for load balancing
- RESTful API for payment operations
- Transaction logging and monitoring
- User authentication and authorization
- Account management
- Payment history tracking

## Architecture
The system follows a microservice architecture with the following components:
- **API Gateway**: Entry point for all requests
- **Auth Service**: Handles user authentication and authorization
- **Account Service**: Manages user accounts and balances
- **Transaction Service**: Processes payment transactions
- **Notification Service**: Sends notifications for completed transactions

## Technologies
- **Backend**: Python with FastAPI
- **Databases**: PostgreSQL for persistent data, Redis for caching
- **Message Queue**: Kafka for asynchronous processing
- **Orchestration**: Kubernetes for container orchestration
- **Service Mesh**: Istio for advanced networking features
- **Monitoring**: Prometheus and Grafana

## Prerequisites
Before running the application, ensure you have the following installed:
- Docker
- Docker Compose

## Getting Started
To run the entire distributed payment system locally using Docker Compose, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/distributed-payment-system.git
    cd distributed-payment-system
    ```

2.  **Start the services:**
    This command will build the necessary Docker images and start all services defined in `docker-compose.yml`.
    ```bash
    docker-compose up --build
    ```

3.  **Access the application:**
    Once all services are up and running, you can access the API Gateway at `http://localhost:8000`.
    The API documentation will be available at `http://localhost:8000/docs`.

## Documentation
- **Installation Guide**: See `docs/installation.md` for setup instructions
- **API Documentation**: Available at `docs/api.md` or at `/docs` when the server is running
- **Testing Documentation**: See `docs/testing.md` for information about test coverage and running tests
- **Contributing Guide**: See `CONTRIBUTING.md` for development setup and guidelines

## Testing
The system includes comprehensive unit tests for all components:

- **Schema Tests**: Validate all data models used in the system
  - Account schemas
  - Transaction schemas
  - User schemas
  - Notification schemas
  - Error handling schemas
  - Pagination schemas
  - Audit log schemas

- **Utility Tests**: Ensure core utility functions work correctly
  - Security utilities (authentication, authorization)
  - Distributed utilities (consistent hashing, locks)
  - Kafka messaging

Run the tests using pytest:
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run specific test modules
pytest tests/unit/common/schemas/test_transactions.py
```

For more detailed testing information, see `docs/testing.md`.

## License
Apache License 2.0. See [LICENSE](LICENSE) file for details.