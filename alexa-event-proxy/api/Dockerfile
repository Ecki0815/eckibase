FROM python:3.12-slim

RUN apt-get update && apt-get upgrade -y && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app app
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8090

CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:8090", "app.app:app"]
