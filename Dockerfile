FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY database.py .
COPY scheduler.py .
COPY manager.py .
COPY webui.py .
COPY templates/ ./templates/
COPY static/ ./static/
COPY entrypoint.sh .

# Install dependencies using uv
RUN uv pip install --system -r pyproject.toml

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Create volume mount point for database persistence
VOLUME /app/data

# Set environment variable for database path
ENV DB_PATH=/app/data/cronishe.db

# Expose webui port
EXPOSE 48080

# Run both scheduler and webui
CMD ["./entrypoint.sh"]
