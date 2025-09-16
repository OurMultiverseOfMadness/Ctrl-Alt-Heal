# Development Guide

This guide provides comprehensive instructions for setting up, developing, and contributing to the Ctrl-Alt-Heal application.

## 🚀 **Quick Start**

### Prerequisites

- **Python 3.12+** (required for Fargate deployment)
- **Node.js 18+** (for CDK)
- **AWS CLI** with configured credentials
- **Docker** (for container builds)
- **Git**

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/Ctrl-Alt-Heal.git
   cd Ctrl-Alt-Heal
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Install CDK dependencies**
   ```bash
   cd cdk
   npm install
   cd ..
   ```

5. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

## 🏗️ **Project Structure**

```
Ctrl-Alt-Heal/
├── src/ctrl_alt_heal/          # Main application code
│   ├── agent/                  # AI agent implementation
│   ├── api/                    # API handlers and validators
│   ├── core/                   # Core services (DI, caching, logging, etc.)
│   ├── domain/                 # Data models and domain logic
│   ├── infrastructure/         # External service integrations
│   ├── interface/              # Interface implementations
│   ├── services/               # Business logic services
│   ├── tools/                  # AI agent tools
│   ├── utils/                  # Utility functions
│   └── worker.py               # Main Lambda handler
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── tools/                  # Tool-specific tests
├── cdk/                        # Infrastructure as Code
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
└── config/                     # Configuration files
```

## 🧪 **Testing**

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ctrl_alt_heal --cov-report=html

# Run specific test categories
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest tests/tools/             # Tool tests only

# Run with verbose output
pytest -v

# Run with parallel execution
pytest -n auto
```

### Test Structure

```python
# Example test structure
class TestUserService:
    def setup_method(self):
        """Setup test fixtures"""
        self.container = get_container()
        self.container.register_singleton('cache_manager', MockCacheManager)
        self.service = self.container.resolve(UserService)

    def test_get_user_success(self):
        """Test successful user retrieval"""
        # Arrange
        user_id = "test-user-123"

        # Act
        result = self.service.get_user(user_id)

        # Assert
        assert result is not None
        assert result.user_id == user_id
```

### Testing Best Practices

- **Use Dependency Injection**: Mock dependencies through the container
- **Test Isolation**: Each test should be independent
- **Arrange-Act-Assert**: Follow the AAA pattern
- **Meaningful Names**: Use descriptive test and method names
- **Coverage**: Aim for >90% code coverage

## 🔧 **Development Workflow**

### Code Quality Tools

```bash
# Linting
flake8 src/ tests/
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Security scanning
bandit -r src/

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

### Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

### Git Workflow

```bash
# Feature development
git checkout -b feature/new-feature
# Make changes
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature

# Create pull request
# Code review and merge
```

## 🏗️ **Architecture Patterns**

### Dependency Injection

```python
# Service registration
from ctrl_alt_heal.core.container import get_container

container = get_container()
container.register_singleton('user_service', UserService)
container.register_factory('logger', lambda: StructuredLogger())

# Service usage
@inject('user_service', 'logger')
def my_function(user_service, logger):
    logger.info("Processing user request")
    return user_service.process_request()
```

### Error Handling

```python
from ctrl_alt_heal.core.error_handling import handle_errors, ErrorContext

@handle_errors
def robust_operation():
    with ErrorContext("user_operation"):
        # Operation code here
        result = perform_operation()
        return result
```

### Caching

```python
from ctrl_alt_heal.core.caching import cache_result

@cache_result(ttl=300)  # 5 minutes
def expensive_operation(user_id: str):
    # Expensive operation here
    return result
```

### Logging

```python
from ctrl_alt_heal.core.logging import get_logger, log_performance

logger = get_logger(__name__)

@log_performance
def tracked_operation():
    logger.info("Starting operation")
    # Operation code
    logger.info("Operation completed")
```

## 🔒 **Security Development**

### Input Validation

```python
from ctrl_alt_heal.core.security_manager import get_security_manager

security = get_security_manager()

def process_user_input(user_input: str):
    # Sanitize input
    clean_input = security.sanitize_input(user_input, level=SecurityLevel.HIGH)

    # Process clean input
    return process_data(clean_input)
```

### Rate Limiting

```python
from ctrl_alt_heal.core.security_manager import rate_limit

@rate_limit(max_requests=100, window_seconds=3600)
def api_endpoint():
    # Endpoint logic here
    pass
```

## 📊 **Monitoring and Observability**

### Health Checks

```python
from ctrl_alt_heal.core.health_monitor import get_health_monitor

monitor = get_health_monitor()

# Register custom health check
def custom_health_check():
    return HealthCheck(
        name="custom_service",
        status=HealthStatus.HEALTHY,
        message="Service is operational"
    )

monitor.register_health_check("custom_service", custom_health_check)
```

### Metrics

```python
from ctrl_alt_heal.core.health_monitor import record_metric

# Record custom metrics
record_metric(
    name="api_response_time",
    value=150.5,
    unit="ms",
    tags={"endpoint": "/api/users"}
)
```

## 🚀 **Local Development**

### **Quick Local Setup**

```bash
# Set up local development environment
python scripts/setup_local_dev.py

# Start local server
python scripts/local_webhook.py
```

The local server will be available at:
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Webhook Endpoint**: http://localhost:8000/webhook

### **Local AWS Services (Optional)**

For complete local development without AWS dependencies:

```bash
# Start LocalStack (DynamoDB, S3, Secrets Manager)
docker run -d \
  --name localstack \
  -p 4566:4566 \
  -p 8000:8000 \
  -e SERVICES=dynamodb,s3,secretsmanager \
  localstack/localstack
```

### **Telegram Webhook Testing**

```bash
# Expose local server with ngrok
ngrok http 8000

# Set webhook to your ngrok URL
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-ngrok-url.ngrok.io/webhook"}'
```

**See [LOCAL_DEVELOPMENT.md](../LOCAL_DEVELOPMENT.md) for complete local development guide.**

## 🔧 **Configuration Management**

### Environment Variables

```bash
# Required environment variables
export AWS_REGION=us-east-1
export TELEGRAM_BOT_TOKEN=your_bot_token
export BEDROCK_MODEL_ID=amazon.nova-1

# Optional environment variables
export LOG_LEVEL=INFO
export CACHE_TTL=300
export SESSION_TIMEOUT_MINUTES=15
```

### Optional Dependencies

The application includes optional dependencies that are not included in the base requirements:

```bash
# For Redis caching (optional)
pip install redis>=5.0.0

# For system monitoring (optional)
pip install psutil>=5.9.0
```

These dependencies are only needed if you want to use:
- **Redis Caching**: For distributed caching across multiple Lambda instances
- **System Monitoring**: For detailed CPU and memory monitoring in health checks

The application gracefully handles missing optional dependencies and falls back to default behavior.

### Feature Flags

```python
from ctrl_alt_heal.core.config_manager import get_config_manager

config = get_config_manager()

# Check feature flag
if config.get('features.new_ui', default=False):
    enable_new_ui()
```

## 🧪 **Testing Strategies**

### Unit Testing

```python
import pytest
from unittest.mock import Mock, patch
from ctrl_alt_heal.core.container import ServiceProvider

class TestUserService:
    def test_get_user_success(self):
        with ServiceProvider() as provider:
            # Arrange
            mock_cache = Mock()
            mock_cache.get.return_value = None
            provider.register_singleton('cache_manager', lambda: mock_cache)

            service = provider.resolve(UserService)

            # Act
            result = service.get_user("user-123")

            # Assert
            assert result is not None
            mock_cache.set.assert_called_once()
```

### Integration Testing

```python
import pytest
from ctrl_alt_heal.infrastructure.users_store import UsersStore

class TestUserIntegration:
    @pytest.fixture
    def users_store(self):
        return UsersStore()

    def test_create_and_retrieve_user(self, users_store):
        # Create user
        user = User(user_id="test-123", first_name="Test")
        users_store.upsert_user(user)

        # Retrieve user
        retrieved = users_store.get_user("test-123")

        assert retrieved is not None
        assert retrieved.first_name == "Test"
```

### Performance Testing

```python
import time
from ctrl_alt_heal.core.logging import PerformanceTracker

def test_performance():
    with PerformanceTracker("test_operation") as tracker:
        # Simulate operation
        time.sleep(0.1)

        # Assert performance
        assert tracker.duration_ms < 200
```

## 🔍 **Debugging**

### Logging Configuration

```python
import logging
from ctrl_alt_heal.core.logging import get_logger

# Configure logging level
logging.getLogger().setLevel(logging.DEBUG)

logger = get_logger(__name__)
logger.debug("Debug information")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Debug Mode

```bash
# Enable debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run with debug output
python -m pytest -s -v
```

### Performance Profiling

```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()

    # Function to profile
    expensive_function()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
```

## 📚 **Documentation**

### Code Documentation

```python
def process_user_data(user_id: str, data: dict) -> dict:
    """
    Process user data with validation and sanitization.

    Args:
        user_id: Unique user identifier
        data: User data to process

    Returns:
        Processed user data

    Raises:
        ValidationError: If data validation fails
        SecurityError: If security check fails

    Example:
        >>> result = process_user_data("user-123", {"name": "John"})
        >>> print(result)
        {'user_id': 'user-123', 'name': 'John', 'processed': True}
    """
    # Implementation here
    pass
```

### API Documentation

```python
from pydantic import BaseModel, Field

class UserCreateRequest(BaseModel):
    """Request model for creating a new user."""

    first_name: str = Field(..., description="User's first name", min_length=1, max_length=50)
    last_name: str = Field(..., description="User's last name", min_length=1, max_length=50)
    timezone: Optional[str] = Field(None, description="User's timezone")

    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "timezone": "America/New_York"
            }
        }
```

## 🚀 **Deployment**

### Local Deployment

```bash
# Deploy to local environment
cd cdk
npm run deploy:local
cd ..
```

### Staging Deployment

```bash
# Deploy to staging
cd cdk
npm run deploy:staging
cd ..
```

### Production Deployment

```bash
# Deploy to production
cd cdk
npm run deploy:production
cd ..
```

## 🔄 **Continuous Integration**

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests
      run: |
        pytest --cov=src/ctrl_alt_heal --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 📋 **Code Review Checklist**

### Before Submitting

- [ ] All tests pass
- [ ] Code coverage >90%
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Security scan passes
- [ ] Documentation updated
- [ ] Performance impact assessed

### Review Criteria

- [ ] Code follows project patterns
- [ ] Error handling is comprehensive
- [ ] Security considerations addressed
- [ ] Performance implications considered
- [ ] Tests are meaningful and complete
- [ ] Documentation is clear and accurate

## 🆘 **Troubleshooting**

### Common Issues

**Import Errors**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**AWS Credentials**
```bash
# Configure AWS credentials
aws configure

# Or use AWS SSO
aws sso login --profile your-profile
```

**Test Failures**
```bash
# Run tests with verbose output
pytest -v -s

# Run specific failing test
pytest tests/unit/test_specific.py::test_function -v -s
```

**Performance Issues**
```bash
# Profile the application
python -m cProfile -o profile.stats your_script.py

# Analyze profile
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"
```

---

## 📚 **Additional Resources**

- [API Reference](./api-reference.md) - Complete API documentation
- [Architecture Guide](./architecture.md) - System architecture details
- [Security Guide](./security.md) - Security best practices
- [Deployment Guide](./deployment.md) - Deployment procedures

---

**Last Updated**: December 2024
**Version**: 2.0.0
**Status**: Production Ready ✅
