# Contributing to the Distributed Payment System

Thank you for your interest in contributing to the Distributed Payment System! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

Please read and adhere to our Code of Conduct to foster an inclusive and respectful community.

## Getting Started

### Setting Up Your Development Environment

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/Distributed-Payment-System.git
   cd Distributed-Payment-System
   ```
3. Set up the development environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Install development dependencies
   ```
4. Start the services using Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Development Workflow

### Branching Strategy

We follow a feature branch workflow:

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```
2. Make your changes in this branch
3. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
4. Create a Pull Request from your branch to the main repository

### Coding Standards

- Follow PEP 8 for Python code style
- Use type hints for function parameters and return values
- Document your code with docstrings
- Write unit tests for new features

We use pre-commit hooks to enforce coding standards. Install them with:

```bash
pip install pre-commit
pre-commit install
```

### Testing

Before submitting a PR, make sure all tests pass:

```bash
pytest
```

For running tests with coverage:

```bash
pytest --cov=app tests/
```

## Pull Request Process

1. Ensure your code follows our coding standards
2. Update documentation if necessary
3. Add tests for new features
4. Make sure all tests pass
5. Update the CHANGELOG.md file if applicable
6. Submit a PR with a clear description of the changes and their purpose

## Distributed System Architecture

When contributing to this project, keep in mind the distributed nature of the system:

- Services should be stateless when possible
- Use Kafka for asynchronous communication between services
- Implement appropriate error handling and retry mechanisms
- Consider the CAP theorem when making design choices

## Technical Documentation

### Adding New Services

If you're adding a new service:

1. Create a new directory under `app/` for your service
2. Create appropriate models, schemas, and API endpoints
3. Update the API Gateway to route requests to your service
4. Add necessary Kubernetes manifests
5. Document the API endpoints

### Database Migrations

For database schema changes:

1. Create a new migration script
2. Test the migration on a development database
3. Document the changes in the PR description

## Getting Help

If you need help with your contribution, you can:

- Open an issue with your questions
- Reach out to the maintainers
- Join our community chat

Thank you for contributing to the Distributed Payment System! 