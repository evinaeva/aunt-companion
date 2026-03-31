#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-/srv/gosha}"
RUN_USER="${2:-$(id -un)}"

sudo mkdir -p /etc/systemd/system

sudo sed \
  -e "s|__PROJECT_ROOT__|$PROJECT_ROOT|g" \
  -e "s|__RUN_USER__|$RUN_USER|g" \
  "$PROJECT_ROOT/deploy/systemd/gosha-llama.service" \
  | sudo tee /etc/systemd/system/gosha-llama.service > /dev/null

sudo sed \
  -e "s|__PROJECT_ROOT__|$PROJECT_ROOT|g" \
  -e "s|__RUN_USER__|$RUN_USER|g" \
  "$PROJECT_ROOT/deploy/systemd/gosha-bot.service" \
  | sudo tee /etc/systemd/system/gosha-bot.service > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable --now gosha-llama.service
sudo systemctl enable --now gosha-bot.service

echo "Installed and started systemd services."
