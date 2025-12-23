FROM python:3.11-slim

WORKDIR /app

# Install specific versions to avoid conflicts
COPY mcp_service/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY mcp_service ./mcp_service

ENV PYTHONPATH=/app:/app/mcp_service
WORKDIR /app/mcp_service

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
