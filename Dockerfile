# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install system dependencies and Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create cache directory for API data
RUN mkdir -p data/cache

# Expose port 5001 for the dashboard
EXPOSE 5001

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash appuser
USER appuser
WORKDIR /home/appuser/app

# Copy application as the appuser
COPY --chown=appuser:appuser . .

# Set environment variables
ENV PYTHONPATH=/home/appuser/app
ENV FLASK_APP=dashboard.app
ENV FLASK_ENV=production

# Create volume for persistent data
VOLUME ["/home/appuser/app/data/cache"]

# Default command to run the dashboard
CMD ["python", "main.py", "dashboard", "--host", "0.0.0.0", "--port", "5001"]