FROM python:3.11-slim AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy requirements and install dependencies (optimize layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code for build stage
COPY app/ app/

# Final runtime stage
FROM python:3.11-slim
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
WORKDIR /app
# Copy application code contents directly into WORKDIR /app
COPY --chown=appuser:appgroup --from=builder /app/app/ .
# Copy installed dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages
# Copy installed executables from builder stage
COPY --from=builder /usr/local/bin /usr/local/bin

# Ensure correct permissions for runtime user (moved here after successful copy)
RUN chown -R appuser:appgroup /app && \
    chown -R appuser:appgroup /usr/local/lib/python3.11/site-packages && \
    chown -R appuser:appgroup /usr/local/bin && chmod -R +r /usr/local/lib/python3.11/site-packages && \
    chmod -R +rx /usr/local/bin

# Expose the required port
EXPOSE 3000

# Run as non-root user
USER appuser

# Start the application using python -m to ensure correct module path
CMD ["python", "-m", "uvicorn", "main:api", "--host", "0.0.0.0", "--port", "3000"] 