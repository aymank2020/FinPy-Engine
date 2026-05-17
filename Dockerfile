FROM python:3.12.7-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pytest==8.3.3 pytest-cov==5.0.0 hypothesis==6.112.1

COPY . /app
RUN pip install /app --no-cache-dir

WORKDIR /app
CMD ["pytest", "/app/tests", "--cov=finpy", "--cov-report=term-missing"]
