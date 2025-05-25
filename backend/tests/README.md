# Backend Testing Guide

This guide provides comprehensive information about testing the Olympian AI Dynamic backend.

## Table of Contents

1. [Test Structure](#test-structure)
2. [Running Tests](#running-tests)
3. [Writing Tests](#writing-tests)
4. [Test Coverage](#test-coverage)
5. [CI/CD Integration](#cicd-integration)
6. [Best Practices](#best-practices)

## Test Structure

The backend test suite is organized as follows:

```
backend/tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Shared fixtures and configuration
├── run_tests.py             # Test runner with coverage support
├── test_discovery.py        # Service discovery tests
├── test_chat_api.py         # Chat API endpoint tests
├── test_config_api.py       # Configuration API tests
├── test_ollama_api.py       # Ollama API endpoint tests
├── test_projects_api.py     # Projects API endpoint tests
├── test_ollama_service.py   # Ollama service unit tests
├── test_websocket.py        # WebSocket functionality tests
└── README.md                # This file
```

## Running Tests

### Prerequisites

Install test dependencies:

```bash
cd backend
pip install -r requirements.txt
```

### Run All Tests

```bash
# From backend directory
python -m pytest tests/

# With coverage
python tests/run_tests.py

# Verbose output
python tests/run_tests.py --no-coverage
```

### Run Specific Test Files

```bash
# Run chat API tests
python tests/run_tests.py chat_api

# Run Ollama service tests
python tests/run_tests.py ollama_service

# Using pytest directly
python -m pytest tests/test_chat_api.py -v
```

### Run Test Categories

```bash
# Run only unit tests
python tests/run_tests.py --unit

# Run only integration tests
python tests/run_tests.py --integration
```

### Using Make Commands

The project includes a Makefile with test commands:

```bash
# Run all tests with coverage
make test

# Run tests and open coverage report
make test-coverage

# Run specific test file
make test-file FILE=test_chat_api.py
```

## Writing Tests

### Test File Naming

- Test files should be named `test_<module_name>.py`
- Test classes should be named `Test<ClassName>`
- Test functions should be named `test_<functionality>`

### Example Test Structure

```python
"""Tests for Example Module"""
import pytest
from unittest.mock import patch, Mock, AsyncMock

from app.api.example import router


@pytest.fixture
def client():
    """Create test client"""
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestExampleAPI:
    """Test suite for Example API"""
    
    def test_get_example(self, client):
        """Test getting example data"""
        response = client.get("/example")
        assert response.status_code == 200
        
    @pytest.mark.asyncio
    async def test_async_operation(self, mock_service):
        """Test async operation"""
        result = await mock_service.async_method()
        assert result is not None
```

### Using Fixtures

Common fixtures are defined in `conftest.py`:

- `mock_settings`: Mocked application settings
- `mock_ollama_service`: Mocked Ollama service
- `mock_project_service`: Mocked project service
- `mock_webhook_service`: Mocked webhook service
- `mock_mcp_service`: Mocked MCP service
- `sample_chat_request`: Sample chat request data
- `sample_conversation`: Sample conversation data
- `sample_project`: Sample project data

### Testing Async Code

Use `pytest.mark.asyncio` decorator for async tests:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected_value
```

### Mocking Dependencies

Use `unittest.mock` for mocking:

```python
from unittest.mock import patch, Mock, AsyncMock

# Mock a synchronous function
with patch('app.module.function', return_value="mocked"):
    result = function_under_test()

# Mock an async function
with patch('app.module.async_function', new=AsyncMock(return_value="mocked")):
    result = await async_function_under_test()
```

## Test Coverage

### Generating Coverage Reports

```bash
# Run tests with coverage
python tests/run_tests.py

# Generate HTML report
coverage html

# View report in browser
open htmlcov/index.html
```

### Coverage Goals

- Aim for at least 80% code coverage
- Focus on critical paths and edge cases
- Don't write tests just for coverage numbers

### Checking Coverage for Specific Modules

```bash
# Check coverage for a specific module
coverage report --include="app/api/chat.py"

# Generate detailed report
coverage report -m
```

## CI/CD Integration

### GitHub Actions

The project uses GitHub Actions for continuous testing. Tests run on:
- Every push to main branch
- Every pull request
- Scheduled daily runs

### Pre-commit Hooks

Install pre-commit hooks to run tests before committing:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Best Practices

### 1. Test Isolation

- Each test should be independent
- Use fixtures for setup and teardown
- Mock external dependencies

### 2. Clear Test Names

```python
# Good
def test_create_project_returns_project_id():
    pass

# Bad
def test_1():
    pass
```

### 3. Arrange-Act-Assert Pattern

```python
def test_example():
    # Arrange
    data = {"name": "test"}
    
    # Act
    result = process_data(data)
    
    # Assert
    assert result["status"] == "success"
```

### 4. Test Edge Cases

- Empty inputs
- Invalid data types
- Boundary values
- Error conditions

### 5. Use Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
])
def test_uppercase(input, expected):
    assert input.upper() == expected
```

### 6. Mock External Services

Always mock external services like:
- Database calls
- HTTP requests
- File system operations
- Third-party APIs

### 7. Test Error Handling

```python
def test_handle_error():
    with pytest.raises(ValueError) as exc_info:
        function_that_raises()
    
    assert "Expected error message" in str(exc_info.value)
```

## Debugging Tests

### Run Tests with Debugging

```bash
# Drop into debugger on failure
python -m pytest tests/ --pdb

# Show print statements
python -m pytest tests/ -s

# Show local variables on failure
python -m pytest tests/ -l
```

### VS Code Configuration

Add to `.vscode/settings.json`:

```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ]
}
```

## Performance Testing

For performance-critical code:

```python
import pytest
import time

def test_performance():
    start = time.time()
    result = expensive_operation()
    duration = time.time() - start
    
    assert duration < 1.0  # Should complete in under 1 second
```

## Integration Testing

Integration tests that require real services should be marked:

```python
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("OLLAMA_HOST"), reason="Ollama not available")
def test_real_ollama_connection():
    # Test with real Ollama instance
    pass
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running tests from the backend directory
2. **Async Warnings**: Use `pytest-asyncio` for async tests
3. **Mock Not Working**: Check patch path matches import path
4. **Fixture Not Found**: Ensure conftest.py is in the tests directory

### Getting Help

- Check test output for detailed error messages
- Use `-v` flag for verbose output
- Check coverage reports for untested code paths
- Review similar test files for examples
