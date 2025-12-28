#!/bin/bash
# Quick Docker validation test (doesn't run full evaluation)

set -e

echo "=== Quick Docker Validation Test ==="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Step 1: Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker daemon is not running. Please start Docker Desktop.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

echo -e "${YELLOW}Step 2: Building Docker image...${NC}"
docker build -t ideation-claude:latest . || {
    echo -e "${RED}✗ Docker build failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Image built successfully${NC}"
echo ""

echo -e "${YELLOW}Step 3: Testing container startup...${NC}"
docker run --rm ideation-claude:latest --help > /dev/null || {
    echo -e "${RED}✗ Container failed to start${NC}"
    exit 1
}
echo -e "${GREEN}✓ Container starts successfully${NC}"
echo ""

echo -e "${YELLOW}Step 4: Testing CLI help output...${NC}"
OUTPUT=$(docker run --rm ideation-claude:latest --help)
if echo "$OUTPUT" | grep -q "Ideation-Claude"; then
    echo -e "${GREEN}✓ CLI help works correctly${NC}"
    echo ""
    echo "Help output preview:"
    echo "$OUTPUT" | head -10
else
    echo -e "${RED}✗ CLI help output incorrect${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 5: Testing with .env file...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file found${NC}"
    
    # Test mounting .env
    docker run --rm \
      -v "$PWD/.env:/app/.env:ro" \
      ideation-claude:latest --help > /dev/null && {
        echo -e "${GREEN}✓ .env file mounts correctly${NC}"
    } || {
        echo -e "${YELLOW}⚠ Warning: .env mounting test failed (may be OK)${NC}"
    }
else
    echo -e "${YELLOW}⚠ .env file not found (create from .env.example)${NC}"
fi
echo ""

echo -e "${GREEN}=== Quick Validation Complete ===${NC}"
echo ""
echo "To run a full evaluation test, use:"
echo "  ./test-docker.sh"
echo ""
echo "Or manually:"
echo "  docker run --rm \\"
echo "    -v \"\$PWD/.env:/app/.env:ro\" \\"
echo "    -v \"\$PWD/reports:/app/reports\" \\"
echo "    ideation-claude:latest \\"
echo "    \"Your startup idea here\""

