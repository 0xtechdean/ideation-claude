#!/bin/bash
# Helper script to set up private repository and secrets

set -e

echo "=== Private Repository Setup Helper ==="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ Warning: .env file not found${NC}"
    echo "Please create .env file from .env.example first"
    exit 1
fi

echo -e "${GREEN}✓ .env file found${NC}"
echo ""

# Check for GitHub CLI
if command -v gh &> /dev/null; then
    echo -e "${GREEN}✓ GitHub CLI found${NC}"
    USE_GH_CLI=true
else
    echo -e "${YELLOW}⚠ GitHub CLI not found${NC}"
    echo "Install with: brew install gh"
    USE_GH_CLI=false
fi

echo ""
echo -e "${BLUE}Step 1: Fork Repository${NC}"
echo "----------------------------------------"
echo "1. Go to: https://github.com/0xtechdean/ideation-claude"
echo "2. Click 'Fork' button"
echo "3. After forking, go to Settings → General → Danger Zone"
echo "4. Click 'Change visibility' → 'Make private'"
echo ""
read -p "Press Enter when you've forked and made it private..."

echo ""
echo -e "${BLUE}Step 2: Get Your Fork URL${NC}"
echo "----------------------------------------"
read -p "Enter your GitHub username: " GITHUB_USERNAME
read -p "Enter your fork name (default: ideation-claude): " FORK_NAME
FORK_NAME=${FORK_NAME:-ideation-claude}
FORK_URL="${GITHUB_USERNAME}/${FORK_NAME}"

echo ""
echo -e "${BLUE}Step 3: Add Secrets${NC}"
echo "----------------------------------------"

if [ "$USE_GH_CLI" = true ]; then
    echo "Using GitHub CLI to set secrets..."
    
    # Read secrets from .env
    ANTHROPIC_KEY=$(grep "^ANTHROPIC_API_KEY=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
    MEM0_KEY=$(grep "^MEM0_API_KEY=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "")
    OPENAI_KEY=$(grep "^OPENAI_API_KEY=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'" || echo "")
    
    if [ -n "$ANTHROPIC_KEY" ]; then
        echo "Setting ANTHROPIC_API_KEY..."
        echo "$ANTHROPIC_KEY" | gh secret set ANTHROPIC_API_KEY --repo "$FORK_URL"
        echo -e "${GREEN}✓ ANTHROPIC_API_KEY set${NC}"
    fi
    
    if [ -n "$MEM0_KEY" ]; then
        echo "Setting MEM0_API_KEY..."
        echo "$MEM0_KEY" | gh secret set MEM0_API_KEY --repo "$FORK_URL"
        echo -e "${GREEN}✓ MEM0_API_KEY set${NC}"
    fi
    
    if [ -n "$OPENAI_KEY" ]; then
        echo "Setting OPENAI_API_KEY..."
        echo "$OPENAI_KEY" | gh secret set OPENAI_API_KEY --repo "$FORK_URL"
        echo -e "${GREEN}✓ OPENAI_API_KEY set${NC}"
    fi
    
    echo ""
    echo "Verifying secrets..."
    gh secret list --repo "$FORK_URL"
else
    echo "Manual setup required:"
    echo ""
    echo "1. Go to: https://github.com/$FORK_URL/settings/secrets/actions"
    echo "2. Click 'New repository secret' for each:"
    echo ""
    
    # Show what to set
    echo "ANTHROPIC_API_KEY=$(grep "^ANTHROPIC_API_KEY=" .env | cut -d'=' -f2- | head -c 20)..."
    if grep -q "^MEM0_API_KEY=" .env; then
        echo "MEM0_API_KEY=$(grep "^MEM0_API_KEY=" .env | cut -d'=' -f2- | head -c 20)..."
    fi
    if grep -q "^OPENAI_API_KEY=" .env; then
        echo "OPENAI_API_KEY=$(grep "^OPENAI_API_KEY=" .env | cut -d'=' -f2- | head -c 20)..."
    fi
    
    echo ""
    read -p "Press Enter when secrets are added..."
fi

echo ""
echo -e "${BLUE}Step 4: Update Remote (Optional)${NC}"
echo "----------------------------------------"
read -p "Update git remote to point to your private fork? (y/n): " UPDATE_REMOTE

if [ "$UPDATE_REMOTE" = "y" ]; then
    git remote set-url origin "https://github.com/$FORK_URL.git"
    echo -e "${GREEN}✓ Remote updated${NC}"
    echo "Current remote:"
    git remote -v
fi

echo ""
echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo "Next steps:"
echo "1. Go to: https://github.com/$FORK_URL/actions"
echo "2. Select 'Ideation Claude Evaluation' workflow"
echo "3. Click 'Run workflow'"
echo "4. Enter your test idea and run!"
echo ""
echo "Or trigger tests:"
echo "  https://github.com/$FORK_URL/actions/workflows/test.yml"

