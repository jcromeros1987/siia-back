FROM python:3.13-slim

# Install uv and system dependencies
RUN pip install --no-cache-dir uv && \
    apt-get update && \
    apt-get install -y --no-install-recommends gcc default-libmysqlclient-dev pkg-config && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy uv.lock and pyproject.toml first for better caching
COPY uv.lock pyproject.toml ./

# Install dependencies with uv
RUN uv sync --frozen

# Copy the rest of the application
COPY . .

CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
