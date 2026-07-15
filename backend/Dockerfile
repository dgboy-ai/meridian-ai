FROM python:3.11-slim

WORKDIR /app

# Copy everything needed for package resolution first
COPY pyproject.toml .
COPY backend/ backend/

# Install Python dependencies
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
