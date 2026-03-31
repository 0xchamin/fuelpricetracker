FROM python:3.12-slim

WORKDIR /code

COPY pyproject.toml .
COPY backend/ backend/
COPY frontend/ frontend/

RUN pip install --no-cache-dir .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9098", "--app-dir", "backend"]
