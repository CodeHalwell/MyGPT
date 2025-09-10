# MyGPT Testing Framework

This document describes the testing setup for the MyGPT application.

## Overview

The project uses **pytest** as the testing framework with coverage reporting. The current test suite achieves **31.22% code coverage**, exceeding the initial target of 30%.

## Test Structure

```
tests/
├── __init__.py              # Test package
├── conftest.py              # Shared test fixtures
├── test_app.py              # App configuration tests
├── test_models.py           # Database model tests
├── test_chat_handler.py     # Chat handler utility tests
└── test_routes_utils.py     # Route utility function tests
```

## Dependencies

The following testing dependencies are included in `pyproject.toml`:

- `pytest>=8.0.0` - Main testing framework
- `pytest-cov>=4.0.0` - Coverage reporting
- `pytest-flask>=1.3.0` - Flask-specific testing utilities

## Running Tests

### Quick Commands

```bash
# Run all tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

# Run specific test file
python -m pytest tests/test_models.py -v

# Run specific test
python -m pytest tests/test_models.py::TestUser::test_user_creation -v
```

### Using the Test Runner

A convenient test runner script is provided:

```bash
# Run tests only
python test_runner.py tests

# Run tests with coverage
python test_runner.py coverage

# Show coverage report only
python test_runner.py coverage-only
```

## Test Coverage

Current coverage by module:

| Module | Coverage | Notes |
|--------|----------|-------|
| models.py | 97.56% | Comprehensive model testing |
| app.py | 86.54% | App configuration and setup |
| routes.py | 30.03% | Utility functions tested |
| multi_provider_chat_handler.py | 29.91% | Basic structure tests |
| email_handler.py | 15.58% | Limited coverage |
| chat_handler.py | 11.21% | Basic configuration tests |

**Total Coverage: 31.22%**

## Test Categories

### Model Tests (`test_models.py`)
- User model creation, password hashing, relationships
- Chat model creation and relationships  
- Message model creation and validation
- Tag model creation and many-to-many relationships
- Database integrity constraints

### App Tests (`test_app.py`)
- Flask app creation and configuration
- Database setup and table creation
- Security settings validation
- Environment variable handling
- Middleware configuration

### Utility Tests
- Color generation functions (`test_routes_utils.py`)
- Model mapping validation (`test_chat_handler.py`)

## Test Configuration

Testing configuration is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
minversion = "8.0"
addopts = "-ra -q --cov=. --cov-report=term-missing --cov-report=html"
testpaths = ["tests"]

[tool.coverage.run]
source = ["."]
omit = ["tests/*", "venv/*", ".venv/*"]

[tool.coverage.report]
precision = 2
show_missing = true
```

## Test Database

Tests use SQLite in-memory databases for isolation:
- Each test gets a fresh database instance
- Temporary files are cleaned up automatically
- Environment variables are set for test mode

## Adding New Tests

1. Create test files in the `tests/` directory following the `test_*.py` naming convention
2. Use the fixtures from `conftest.py` for common setup (app, client, sample data)
3. Follow the existing patterns for database tests
4. Run tests to ensure they pass and contribute to coverage

## CI/CD Integration

The testing framework is ready for CI/CD integration:
- All dependencies are specified in `pyproject.toml`
- Tests are isolated and don't require external services
- Coverage reports are generated in both terminal and HTML formats
- Exit codes are properly handled for automation

## Future Enhancements

To increase coverage further, consider adding:
- Integration tests for API endpoints
- Tests for AI provider integrations (with mocking)
- Email functionality tests (with mocking)
- Authentication flow tests
- Error handling tests