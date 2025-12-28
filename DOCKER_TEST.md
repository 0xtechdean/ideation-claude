# Docker Testing Guide

This guide helps you test the Docker setup for ideation-claude.

## Prerequisites

1. **Docker Desktop** must be installed and running
2. **.env file** must be configured with your API keys (copy from `.env.example`)

## Quick Validation Test

Run a quick test that validates the Docker setup without running a full evaluation:

```bash
./test-docker-quick.sh
```

This will:
- ✅ Check Docker is running
- ✅ Build the Docker image
- ✅ Test container startup
- ✅ Verify CLI help works
- ✅ Test .env file mounting

## Full Evaluation Test

To test with an actual idea evaluation:

```bash
./test-docker.sh
```

Or manually:

```bash
# Build the image
docker build -t ideation-claude:latest .

# Run evaluation
docker run --rm \
  -v "$PWD/.env:/app/.env:ro" \
  -v "$PWD/reports:/app/reports" \
  ideation-claude:latest \
  "AI-powered personal finance assistant"
```

## Using Docker Compose

```bash
# Build and run
docker-compose run --rm ideation-claude "Your startup idea"

# With options
docker-compose run --rm ideation-claude \
  --threshold 6.0 \
  --subagent \
  "Your startup idea"
```

## Expected Output

After running an evaluation, you should see:

1. **Console output** showing progress through the pipeline phases
2. **Report file** in `reports/` directory (named based on the idea)
3. **Summary** showing:
   - Total ideas evaluated
   - Passed vs eliminated
   - Scores

## Troubleshooting

### Docker daemon not running
```bash
# Start Docker Desktop, then verify:
docker info
```

### Build fails
```bash
# Check Dockerfile syntax:
docker build --no-cache -t ideation-claude:latest .
```

### Container can't access .env
```bash
# Ensure .env file exists and has correct permissions:
ls -la .env
chmod 644 .env
```

### API key errors
```bash
# Verify .env file has valid keys:
grep ANTHROPIC_API_KEY .env
```

### Reports not appearing
```bash
# Check reports directory exists and is writable:
mkdir -p reports
chmod 755 reports
```

## Validation Checklist

- [ ] Docker Desktop is running
- [ ] Image builds successfully
- [ ] Container starts and shows help
- [ ] .env file mounts correctly
- [ ] Reports directory is created
- [ ] Evaluation completes successfully
- [ ] Report file is generated
- [ ] Report contains expected sections

## Test Ideas

Use these simple test ideas for validation:

1. "AI-powered personal finance assistant"
2. "Sustainable packaging marketplace"
3. "Remote team collaboration tool"

Note: Full evaluations use API credits and may take several minutes.

