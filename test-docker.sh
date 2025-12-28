#!/bin/bash
# Test script for Docker setup

set -e

echo "=== Testing Ideation-Claude Docker Setup ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test idea
TEST_IDEA="AI-powered personal finance assistant"

echo -e "${YELLOW}Step 1: Building Docker image...${NC}"
docker build -t ideation-claude:latest . || {
    echo -e "${RED}Error: Docker build failed. Make sure Docker is running.${NC}"
    exit 1
}

echo -e "${GREEN}✓ Docker image built successfully${NC}"
echo ""

echo -e "${YELLOW}Step 2: Creating reports directory...${NC}"
mkdir -p reports
echo -e "${GREEN}✓ Reports directory ready${NC}"
echo ""

echo -e "${YELLOW}Step 3: Running evaluation with test idea...${NC}"
echo -e "Test idea: ${TEST_IDEA}"
echo ""

# Run the evaluation
docker run --rm \
  -v "$PWD/.env:/app/.env:ro" \
  -v "$PWD/reports:/app/reports" \
  -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-$(grep ANTHROPIC_API_KEY .env | cut -d '=' -f2)}" \
  -e MEM0_API_KEY="${MEM0_API_KEY:-$(grep MEM0_API_KEY .env | cut -d '=' -f2 || echo '')}" \
  -e OPENAI_API_KEY="${OPENAI_API_KEY:-$(grep OPENAI_API_KEY .env | cut -d '=' -f2 || echo '')}" \
  ideation-claude:latest \
  --quiet --threshold 5.0 "$TEST_IDEA" --output "reports/test_output.md" || {
    echo -e "${RED}Error: Docker run failed${NC}"
    exit 1
}

echo ""
echo -e "${YELLOW}Step 4: Validating output...${NC}"

# Check if report was created
if [ -f "reports/test_output.md" ]; then
    echo -e "${GREEN}✓ Report file created: reports/test_output.md${NC}"
    echo ""
    echo "=== Report Preview (first 50 lines) ==="
    head -50 reports/test_output.md
    echo ""
    echo "=== Report Statistics ==="
    echo "File size: $(wc -c < reports/test_output.md) bytes"
    echo "Line count: $(wc -l < reports/test_output.md) lines"
    echo ""
    
    # Check for key sections
    if grep -q "Research\|Competitor\|Market\|Hypothesis\|Score" reports/test_output.md; then
        echo -e "${GREEN}✓ Report contains expected sections${NC}"
    else
        echo -e "${YELLOW}⚠ Warning: Report may be missing some sections${NC}"
    fi
else
    echo -e "${RED}✗ Error: Report file not found${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Docker Test Completed Successfully ===${NC}"

