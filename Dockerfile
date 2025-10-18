# Builder stage
FROM python:3.10-slim AS builder

WORKDIR /src

# Install uv (modern pip replacement)
RUN pip install --upgrade pip
RUN pip install --no-cache-dir uv

# Copy requirements file
COPY requirements.txt .

# Create venv and install dependencies
RUN uv venv
RUN . .venv/bin/activate && uv pip install --upgrade pip && uv pip install -r requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /src

# Copy venv from builder
COPY --from=builder /src/.venv /src/.venv

# Copy application files
COPY . .

# Activate virtual environment and set PYTHONPATH
ENV PATH="/src/.venv/bin:$PATH"
ENV PYTHONPATH="/src"
ENV PORT=8000

# Use ENTRYPOINT to run gunicorn with multi worker for production
ENTRYPOINT ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "gunicorn_conf.py", "src.main:app"]