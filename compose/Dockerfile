FROM python:3.9.13-slim

WORKDIR /app

COPY ./ ./

RUN apt-get update && apt-get install -y \
    build-essential \
    software-properties-common \
    unixodbc-dev \
    gnupg2 \
    curl \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get clean

RUN pip install -r compose/requirements.txt

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "snow_questions.py", "--server.port=8501", "--server.address=0.0.0.0"]
