#!/bin/bash
echo "=== Validating GitHub Actions Workflow ==="
echo ""

# Check workflow file exists
if [ ! -f ".github/workflows/test.yml" ]; then
    echo "✗ Workflow file not found"
    exit 1
fi
echo "✓ Workflow file exists"

# Check for required sections
if grep -q "pytest tests/" .github/workflows/test.yml; then
    echo "✓ Test command found"
else
    echo "✗ Test command missing"
    exit 1
fi

if grep -q "python-version:" .github/workflows/test.yml; then
    echo "✓ Python version matrix found"
else
    echo "✗ Python version matrix missing"
    exit 1
fi

if grep -q "pip install -e" .github/workflows/test.yml; then
    echo "✓ Package installation found"
else
    echo "✗ Package installation missing"
    exit 1
fi

echo ""
echo "✓ Workflow validation passed"
echo ""
echo "Workflow will run on:"
grep -A 1 "python-version:" .github/workflows/test.yml | grep -E "3\.(10|11|12)" | sed 's/.*"\(.*\)".*/  - Python \1/'
