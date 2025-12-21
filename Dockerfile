FROM debian:trixie-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3 \
    python3-venv \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY app.py camera.py main.py ./

CMD ["python3", "main.py"]
