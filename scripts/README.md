# Utility Scripts

This directory contains utility scripts for development, deployment, and maintenance tasks.

## Scripts

### Development & Quality
- **`run_quality_checks.sh`** - Comprehensive code quality checks (linting, testing, type checking)
- **`check_git_status.sh`** - Git status validation and pre-commit security checks

### Secret Management
- **`update_serper_secret.py`** - Update Serper API key in AWS Secrets Manager
- **`update_telegram_secret.py`** - Update Telegram bot token in AWS Secrets Manager

## Usage

### Quality Checks
```bash
# Run all quality checks
./scripts/run_quality_checks.sh

# Check git status before committing
./scripts/check_git_status.sh
```

### Secret Management
```bash
# Update Serper API key
python scripts/update_serper_secret.py

# Update Telegram bot token
python scripts/update_telegram_secret.py
```

## Quality Checks

The quality check script performs:
- **Testing**: Run comprehensive test suite
- **Linting**: Code style and quality checks
- **Type Checking**: Static type analysis
- **Import Validation**: Check for missing imports
- **Error Pattern Detection**: Common error pattern identification

## Benefits

- **Automated Quality**: Consistent code quality across the project
- **Pre-commit Validation**: Catch issues before committing
- **CI/CD Integration**: Ready for continuous integration pipelines
- **Developer Productivity**: Streamlined development workflow
