#!/usr/bin/env bash

# Quality Check Script for Ctrl-Alt-Heal
# This script runs comprehensive tests, linting, and type checking

set -e  # Exit on any error

echo "🔍 Running Quality Checks for Ctrl-Alt-Heal"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "Virtual environment not detected. Please activate your virtual environment first."
    print_status "Run: source venv/bin/activate"
    exit 1
fi

print_success "Virtual environment detected: $VIRTUAL_ENV"

# 0. Show what files will be checked
print_status "Files to be checked:"
echo "  📁 Source files: src/"
echo "  🧪 Test files: tests/"
echo "  📄 Config files: *.py, *.md, *.yaml, *.yml, *.json, *.toml, *.sh"
echo "  🚫 Excluded: build/, packaging/, lambda_layer/, venv/, cache directories"

# 1. Install required packages for type checking
print_status "Installing type checking dependencies..."
pip install -q mypy types-requests types-PyYAML types-pytz

# 2. Run pre-commit hooks (only on source files)
print_status "Running pre-commit hooks on source files..."
if pre-commit run --files src/ tests/ *.py *.md *.yaml *.yml *.json *.toml *.sh; then
    print_success "Pre-commit hooks passed"
else
    print_error "Pre-commit hooks failed"
    exit 1
fi

# 3. Run unit tests
print_status "Running unit tests..."
if python -m pytest tests/ -v --tb=short; then
    print_success "Unit tests passed"
else
    print_error "Unit tests failed"
    exit 1
fi

# 4. Run type checking (only on source files)
print_status "Running type checking on source files..."
if python -m mypy src/ --ignore-missing-imports --no-strict-optional --exclude ".*/(venv|\.venv|node_modules|\.git|\.pytest_cache|\.mypy_cache|\.ruff_cache|__pycache__|build|dist|packaging|lambda_layer|cdk/lambda_layer|infra/lambda_layers)/.*"; then
    print_success "Type checking passed"
else
    print_warning "Type checking found issues (see above for details)"
    print_status "Consider fixing type issues for better code quality"
fi

# 5. Check for common import issues
print_status "Checking for common import issues..."
python -c "
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

# Test critical imports
try:
    import ctrl_alt_heal.worker
    import ctrl_alt_heal.agent.care_companion
    import ctrl_alt_heal.infrastructure.identities_store
    import ctrl_alt_heal.infrastructure.users_store
    print('✅ Critical imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

# 6. Check for missing environment variables in code (only source files)
print_status "Checking for hardcoded environment variable access in source files..."
if grep -r "os\.environ\[" src/ | grep -v "os\.environ\.get" | grep -v "getenv"; then
    print_warning "Found direct os.environ access (consider using .get() for safety)"
else
    print_success "No direct os.environ access found"
fi

# 7. Check for common error patterns (only source files)
print_status "Checking for common error patterns in source files..."

# Check for missing imports in source files only
if grep -r "NameError.*not defined" src/ tests/ 2>/dev/null || true; then
    print_warning "Found potential NameError patterns in source files"
fi

# Check for missing os import in source files only
if grep -r "os\." src/ | grep -v "import os" | grep -v "from.*import.*os" | head -5; then
    print_warning "Found os usage without import (check for missing 'import os')"
fi

# Check for other common missing imports in source files
print_status "Checking for other common missing imports..."
for import_check in "json\." "datetime\." "logging\." "boto3\." "requests\."; do
    import_name=$(echo "$import_check" | sed 's/\\\.//')
    if grep -r "$import_check" src/ | grep -v "import $import_name" | grep -v "from.*import.*$import_name" | head -3; then
        print_warning "Found $import_name usage without import"
    fi
done

# 8. Summary
echo ""
echo "🎉 Quality Check Summary"
echo "======================="
print_success "All quality checks completed"
print_status "Next steps:"
echo "  - Fix any type issues identified by mypy"
echo "  - Address any warnings from pre-commit hooks"
echo "  - Run this script before committing changes"
echo "  - Consider adding this to your CI/CD pipeline"

print_status "To run individual checks:"
echo "  - Tests: python -m pytest tests/ -v"
echo "  - Linting: pre-commit run --files src/ tests/ *.py *.md *.yaml *.yml *.json *.toml *.sh"
echo "  - Type checking: python -m mypy src/ --ignore-missing-imports --exclude '.*/(venv|\.venv|node_modules|\.git|\.pytest_cache|\.mypy_cache|\.ruff_cache|__pycache__|build|dist|packaging|lambda_layer|cdk/lambda_layer|infra/lambda_layers)/.*'"
