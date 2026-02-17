FROM debian:trixie-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    python3-venv \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy everything into container
COPY . .

# Optional: install Python deps if you have requirements.txt
# RUN pip3 install -r requirements.txt

CMD ["python3", "main.py"]
