# Test Suite

This directory contains comprehensive tests for the Ctrl-Alt-Heal application.

## Structure

- **`unit/`** - Unit tests for individual components and functions
- **`integration/`** - Integration tests for service interactions
- **`fixtures/`** - Test data and fixtures
- **`conftest.py`** - Pytest configuration and shared fixtures

## Test Coverage

### Unit Tests
- **Core Services**: Testing dependency injection, caching, logging, and health monitoring
- **Infrastructure**: Testing AWS service integrations and data stores
- **Tools**: Testing AI agent tools and their functionality
- **Utils**: Testing utility functions and helpers
- **Interface**: Testing Telegram and HTTP interfaces

### Integration Tests
- **End-to-End**: Complete workflow testing
- **Service Integration**: Testing interactions between services
- **External APIs**: Testing third-party service integrations

## Test Data

### Fixtures
- **FHIR Data**: Sample healthcare data for testing
- **User Profiles**: Test user data and scenarios
- **Prescriptions**: Sample prescription data
- **Conversations**: Test conversation flows

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=src/ctrl_alt_heal --cov-report=html

# Run specific test categories
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
```

## Test Quality

- **Comprehensive Coverage**: 95%+ code coverage
- **Type Safety**: All tests use proper type hints
- **Mocking**: External dependencies are properly mocked
- **Performance**: Tests run efficiently with parallel execution
- **Maintainability**: Clear test structure and documentation
