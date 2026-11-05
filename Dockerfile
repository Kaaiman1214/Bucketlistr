FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    BUCKETLIST_HOST=0.0.0.0 \
    BUCKETLIST_PORT=5000 \
    BUCKETLIST_DATA_DIR=/data

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY website ./website

RUN useradd --system --uid 1000 --no-create-home bucketlist \
    && mkdir /data \
    && chown bucketlist /data

USER bucketlist

VOLUME /data
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ['BUCKETLIST_PORT'] + '/')"]

CMD ["python", "main.py"]
