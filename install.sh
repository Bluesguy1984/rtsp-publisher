#!/usr/bin/env bash
set -e

APP_NAME="rtsp-publisher"
REPO_URL="https://github.com/Bluesguy1984/rtsp-publisher.git"
INSTALL_DIR="/opt/${APP_NAME}"
MEDIAMTX_VERSION="1.8.4"

echo "=========================================="
echo " Installing RTSP Publisher"
echo "=========================================="

# Require root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

echo "[1/6] Updating system..."
apt update
apt upgrade -y

echo "[2/6] Installing dependencies..."
apt install -y git curl tar

if ! command -v docker &> /dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  usermod -aG docker $SUDO_USER || true
fi

echo "[3/6] Installing MediaMTX..."

if [ ! -f /usr/local/bin/mediamtx ]; then
  curl -L \
    https://github.com/bluenviron/mediamtx/releases/download/v${MEDIAMTX_VERSION}/mediamtx_v${MEDIAMTX_VERSION}_linux_arm64.tar.gz \
    -o /tmp/mediamtx.tar.gz

  tar -xzf /tmp/mediamtx.tar.gz -C /tmp
  mv /tmp/mediamtx /usr/local/bin/
  chmod +x /usr/local/bin/mediamtx
fi

cat >/etc/systemd/system/mediamtx.service <<EOF
[Unit]
Description=MediaMTX RTSP Server
After=network.target

[Service]
ExecStart=/usr/local/bin/mediamtx
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable mediamtx
systemctl restart mediamtx

echo "[4/6] Installing RTSP Publisher..."

rm -rf ${INSTALL_DIR}
git clone ${REPO_URL} ${INSTALL_DIR}

cd ${INSTALL_DIR}

echo "[5/6] Building Docker container..."
docker compose build --no-cache

echo "[6/6] Starting container..."
docker compose up -d

echo "=========================================="
echo " Installation Complete"
echo "=========================================="

echo "MediaMTX running on port 8554"
echo "Health endpoint: http://$(hostname -I | awk '{print $1}'):9188/health"
echo ""
echo "Log viewer:"
echo "docker logs -f rtsp-publisher"
echo ""
echo "IMPORTANT: Log out and back in to use Docker without sudo."
