FROM python:3.12.7-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app
RUN python -m pip wheel . --no-deps --no-cache-dir --wheel-dir /tmp/wheels \
    && python -c "from pathlib import Path; import subprocess, sys; wheel, = Path('/tmp/wheels').glob('finpy-*.whl'); subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', str(wheel) + '[dev]'], check=True)"

CMD ["python", "-m", "pytest", "-ra", "/app/tests", "--cov=finpy", "--cov-report=term-missing", "--cov-fail-under=95"]
