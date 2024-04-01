FROM python:3.9.13-slim

WORKDIR /especialidades-app

COPY requirements.txt ./

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        unixodbc-dev \
        gnupg2 \
        curl \
    && curl -s https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl -s https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    # Clean up in the same layer to reduce image size
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "especialidades.py", "--server.port=8501", "--server.address=0.0.0.0"]

