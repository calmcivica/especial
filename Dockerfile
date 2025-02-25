# Build stage
FROM python:3.9.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gnupg2 \
    curl \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft repos for ODBC Driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.9.13-slim

WORKDIR /especialidades-app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg2 \
    curl \
    unixodbc \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy built packages from builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create necessary directories
RUN mkdir -p /especialidades-app/jsons /especialidades-app/static /especialidades-app/sql_especialidad

# Copy application code
COPY *.py ./
COPY ./jsons/*.json ./jsons/
COPY ./sql_especialidad/*.py ./sql_especialidad/
COPY ./.streamlit ./.streamlit
COPY ./static ./static
COPY requirements.txt ./

# Create a non-root user
RUN useradd -m appuser
RUN chown -R appuser:appuser /especialidades-app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s CMD curl --fail http://localhost:8501/_stcore/health || exit 1

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "especialidades.py", "--server.port=8501", "--server.address=0.0.0.0"]