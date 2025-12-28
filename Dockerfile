# Multi-stage build for Ideation-Claude
FROM python:3.10-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and source code
COPY pyproject.toml ./
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir --user -e .

# Final stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed package from builder
COPY --from=builder /root/.local /root/.local

# Copy application code (needed for runtime)
COPY src/ ./src/
COPY pyproject.toml ./

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Create directories for outputs
RUN mkdir -p /app/reports /app/output /app/context

# Set working directory
WORKDIR /app

# Default command
ENTRYPOINT ["ideation-claude"]
CMD ["--help"]

