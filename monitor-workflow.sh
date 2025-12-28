#!/bin/bash
# Monitor GitHub Actions workflow execution

set -e

REPO="${1:-Othentic-Ai/ideation-claude}"
WORKFLOW="${2:-ideation.yml}"

echo "=== Monitoring Workflow: $WORKFLOW ==="
echo "Repository: $REPO"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get latest run
LATEST_RUN=$(gh run list --repo "$REPO" --workflow "$WORKFLOW" --limit 1 --json databaseId --jq '.[0].databaseId' 2>/dev/null)

if [ -z "$LATEST_RUN" ]; then
    echo -e "${RED}No workflow runs found${NC}"
    exit 1
fi

echo -e "${BLUE}Latest Run ID: $LATEST_RUN${NC}"
echo ""

# Get run details
RUN_INFO=$(gh run view $LATEST_RUN --repo "$REPO" --json status,conclusion,createdAt,updatedAt,displayTitle,url,headBranch)
STATUS=$(echo "$RUN_INFO" | jq -r '.status')
CONCLUSION=$(echo "$RUN_INFO" | jq -r '.conclusion // "running"')
TITLE=$(echo "$RUN_INFO" | jq -r '.displayTitle')
URL=$(echo "$RUN_INFO" | jq -r '.url')
CREATED=$(echo "$RUN_INFO" | jq -r '.createdAt')
BRANCH=$(echo "$RUN_INFO" | jq -r '.headBranch')

echo -e "${BLUE}Run Details:${NC}"
echo "  Title: $TITLE"
echo "  Branch: $BRANCH"
echo "  Status: $STATUS"
echo "  Conclusion: $CONCLUSION"
echo "  Created: $CREATED"
echo "  URL: $URL"
echo ""

# Get job status
echo -e "${BLUE}Job Status:${NC}"
gh api repos/$REPO/actions/runs/$LATEST_RUN/jobs --jq '.jobs[] | "  \(.name): \(.status) - \(.conclusion // "running")"' 2>/dev/null || echo "  Unable to fetch job status"
echo ""

# Show recent log output
if [ "$STATUS" = "in_progress" ] || [ "$STATUS" = "queued" ]; then
    echo -e "${YELLOW}Workflow is still running...${NC}"
    echo ""
    echo "Recent log output (last 30 lines):"
    echo "-----------------------------------"
    gh run view $LATEST_RUN --repo "$REPO" --log 2>&1 | tail -30 || echo "Logs not available yet"
    echo ""
    echo -e "${BLUE}To watch in real-time:${NC}"
    echo "  gh run watch $LATEST_RUN --repo $REPO"
    echo ""
    echo -e "${BLUE}Or view in browser:${NC}"
    echo "  $URL"
else
    echo -e "${BLUE}Workflow completed: $CONCLUSION${NC}"
    echo ""
    echo "Final log output (last 50 lines):"
    echo "-----------------------------------"
    gh run view $LATEST_RUN --repo "$REPO" --log 2>&1 | tail -50
    echo ""
    
    if [ "$CONCLUSION" = "success" ]; then
        echo -e "${GREEN}✓ Workflow completed successfully!${NC}"
        echo ""
        echo "Download artifacts:"
        gh run view $LATEST_RUN --repo "$REPO" --json artifacts --jq '.artifacts[] | "  - \(.name) (\(.size_in_bytes) bytes)"' 2>/dev/null || echo "  No artifacts found"
    else
        echo -e "${RED}✗ Workflow failed${NC}"
        echo ""
        echo "Failed steps:"
        gh api repos/$REPO/actions/runs/$LATEST_RUN/jobs --jq '.jobs[0].steps[] | select(.conclusion == "failure") | "  - \(.name)"' 2>/dev/null || echo "  Unable to fetch failed steps"
    fi
fi

