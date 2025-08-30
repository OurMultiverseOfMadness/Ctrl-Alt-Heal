#!/usr/bin/env bash

# Git Status Check Script for Ctrl-Alt-Heal
# This script checks what files are staged and warns about potentially sensitive files

set -e

echo "🔍 Checking Git Status for Ctrl-Alt-Heal"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository"
    exit 1
fi

print_success "Git repository detected"

# Check staged files
print_status "Checking staged files..."
STAGED_FILES=$(git diff --cached --name-only)

if [ -z "$STAGED_FILES" ]; then
    print_warning "No files are currently staged for commit"
    print_status "Run 'git add <files>' to stage files for commit"
    exit 0
fi

echo ""
print_status "Staged files:"
echo "$STAGED_FILES" | while read -r file; do
    if [ -n "$file" ]; then
        echo "  📄 $file"
    fi
done

echo ""
print_status "Checking for potentially sensitive files..."

# Check for sensitive files
SENSITIVE_PATTERNS=(
    "*.env"
    "*.key"
    "*.pem"
    "*.crt"
    "*.p12"
    "*.pfx"
    "client_secret.json"
    "secrets/"
    "credentials/"
    "*.log"
    "*.tmp"
    "*.temp"
    "*.bak"
    "*.backup"
    "__pycache__/"
    ".pytest_cache/"
    ".mypy_cache/"
    ".ruff_cache/"
    "venv/"
    ".venv/"
    "node_modules/"
    ".cdk.staging/"
    "cdk.out/"
    "packaging/"
    "lambda_layer/"
    "cdk/lambda_layer/"
    "infra/lambda_layers/"
)

SENSITIVE_FOUND=false

for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if echo "$STAGED_FILES" | grep -q "$pattern"; then
        print_warning "Potentially sensitive file found: $pattern"
        SENSITIVE_FOUND=true
    fi
done

if [ "$SENSITIVE_FOUND" = false ]; then
    print_success "No sensitive files detected in staged files"
fi

echo ""
print_status "Checking file sizes..."

# Check for large files
LARGE_FILES=$(git diff --cached --name-only | xargs -I {} sh -c 'if [ -f "{}" ]; then echo "{}: $(du -h "{}" | cut -f1)"; fi' 2>/dev/null || true)

if [ -n "$LARGE_FILES" ]; then
    echo "$LARGE_FILES" | while read -r file_info; do
        if [ -n "$file_info" ]; then
            size=$(echo "$file_info" | cut -d: -f2 | sed 's/[^0-9.]//g')
            if [ "$(echo "$size > 10" | bc -l 2>/dev/null || echo "0")" = "1" ]; then
                print_warning "Large file detected: $file_info"
            else
                echo "  📄 $file_info"
            fi
        fi
    done
fi

echo ""
print_status "Checking for binary files..."

# Check for binary files
BINARY_FILES=$(git diff --cached --name-only | xargs -I {} sh -c 'if [ -f "{}" ] && file "{}" | grep -q "binary"; then echo "{}"; fi' 2>/dev/null || true)

if [ -n "$BINARY_FILES" ]; then
    print_warning "Binary files detected:"
    echo "$BINARY_FILES" | while read -r file; do
        if [ -n "$file" ]; then
            echo "  🔧 $file"
        fi
    done
else
    print_success "No binary files detected"
fi

echo ""
print_status "Checking for common issues..."

# Check for common issues
if echo "$STAGED_FILES" | grep -q "\.py$"; then
    # Check for missing imports in Python files
    for file in $(echo "$STAGED_FILES" | grep "\.py$"); do
        if [ -f "$file" ]; then
            # Check for os.environ usage without import
            if grep -q "os\." "$file" && ! grep -q "import os" "$file" && ! grep -q "from.*import.*os" "$file"; then
                print_warning "Potential missing 'import os' in $file"
            fi

            # Check for other common missing imports
            if grep -q "json\." "$file" && ! grep -q "import json" "$file"; then
                print_warning "Potential missing 'import json' in $file"
            fi

            if grep -q "datetime\." "$file" && ! grep -q "import datetime" "$file" && ! grep -q "from datetime" "$file"; then
                print_warning "Potential missing datetime import in $file"
            fi
        fi
    done
fi

echo ""
print_status "Summary:"
echo "  📊 Total staged files: $(echo "$STAGED_FILES" | wc -l | tr -d ' ')"
echo "  🔍 Run 'git diff --cached' to see changes"
echo "  🚀 Run 'git commit' to commit staged files"

if [ "$SENSITIVE_FOUND" = true ]; then
    echo ""
    print_warning "⚠️  WARNING: Sensitive files detected!"
    print_status "Please review staged files before committing."
    print_status "Consider adding sensitive files to .gitignore"
    exit 1
else
    echo ""
    print_success "✅ All checks passed! Ready to commit."
fi
