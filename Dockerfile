FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/

# Expose port
EXPOSE 3000

# Run the application with Uvicorn
CMD ["uvicorn", "app.main:api", "--host", "0.0.0.0", "--port", "3000"] 