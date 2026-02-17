#!/usr/bin/env bash
set -e

APP_NAME="rtsp-publisher"
REPO_URL="https://github.com/Bluesguy1984/rtsp-publisher.git"
INSTALL_DIR="/opt/${APP_NAME}"

echo "=========================================="
echo " RTSP Publisher Production Installer"
echo "=========================================="

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo."
  exit 1
fi

echo "[1/7] Updating system..."
apt update -y
apt upgrade -y

echo "[2/7] Installing base dependencies..."
apt install -y git curl tar jq

echo "[3/7] Installing Docker (if needed)..."
if ! command -v docker &> /dev/null; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
fi

echo "[4/7] Installing MediaMTX..."

ARCH=$(uname -m)

if [ "$ARCH" = "aarch64" ]; then
  MTX_ARCH="linux_arm64"
elif [ "$ARCH" = "armv7l" ]; then
  MTX_ARCH="linux_armv7"
else
  echo "Unsupported architecture: $ARCH"
  exit 1
fi

LATEST_VERSION=$(curl -s https://api.github.com/repos/bluenviron/mediamtx/releases/latest | jq -r .tag_name)

if [ -z "$LATEST_VERSION" ] || [ "$LATEST_VERSION" = "null" ]; then
  echo "Failed to determine latest MediaMTX version."
  exit 1
fi

MTX_URL="https://github.com/bluenviron/mediamtx/releases/download/${LATEST_VERSION}/mediamtx_${LATEST_VERSION}_${MTX_ARCH}.tar.gz"

echo "Downloading MediaMTX ${LATEST_VERSION} for ${MTX_ARCH}..."
curl -L -o /tmp/mediamtx.tar.gz "$MTX_URL"

file /tmp/mediamtx.tar.gz | grep -q gzip || {
  echo "Download failed or incorrect architecture."
  exit 1
}

tar -xzf /tmp/mediamtx.tar.gz -C /tmp
mv /tmp/mediamtx /usr/local/bin/
chmod +x /usr/local/bin/mediamtx
rm /tmp/mediamtx.tar.gz

echo "Creating systemd service for MediaMTX..."

cat >/etc/systemd/system/mediamtx.service <<EOF
[Unit]
Description=MediaMTX RTSP Server
After=network.target

[Service]
ExecStart=/usr/local/bin/mediamtx
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable mediamtx
systemctl restart mediamtx

echo "[5/7] Installing RTSP Publisher..."

rm -rf ${INSTALL_DIR}
git clone ${REPO_URL} ${INSTALL_DIR}

cd ${INSTALL_DIR}

echo "[6/7] Building Docker container..."
docker compose build --no-cache

echo "[7/7] Starting container..."
docker compose up -d

IP_ADDR=$(hostname -I | awk '{print $1}')

echo "=========================================="
echo " INSTALLATION COMPLETE"
echo "=========================================="
echo ""
echo "RTSP Stream:"
echo "  rtsp://${IP_ADDR}:8554/camera?tcp"
echo ""
echo "Health Endpoint:"
echo "  http://${IP_ADDR}:9188/health"
echo ""
echo "View Logs:"
echo "  docker logs -f rtsp-publisher"
echo ""
echo "MediaMTX Status:"
echo "  systemctl status mediamtx"
echo ""
echo "Reboot to verify auto-start functionality."
echo "=========================================="
