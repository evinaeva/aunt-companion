# Server quickstart (Ubuntu)

## 1. Create project root
```bash
sudo mkdir -p /srv/gosha
sudo chown -R "$USER":"$USER" /srv/gosha
cd /srv/gosha
```

## 2. Unpack this archive into `/srv/gosha`

## 3. Create base tree
```bash
chmod +x scripts/*.sh
./scripts/00_create_project_tree.sh /srv/gosha
```

## 4. Install packages and build llama.cpp
```bash
./scripts/01_bootstrap_ubuntu.sh /srv/gosha
```

## 5. Download models
```bash
./scripts/02_download_models.sh /srv/gosha
```

## 6. Create `.env`
```bash
./scripts/03_create_env.sh /srv/gosha
nano /srv/gosha/.env
```

Fill in:
- `TELEGRAM_BOT_TOKEN`
- `ALLOWED_TELEGRAM_USER_IDS`
- `ADMIN_TELEGRAM_USER_ID`

## 7. Start manually
```bash
./scripts/04_start_llama_server.sh /srv/gosha
# open second shell
./scripts/05_run_bot.sh /srv/gosha
```

## 8. Or install systemd
```bash
./scripts/06_install_systemd.sh /srv/gosha "$USER"
```

## 9. Check logs
```bash
journalctl -u gosha-llama -f
journalctl -u gosha-bot -f
```
