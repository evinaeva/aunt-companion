# Server quickstart (Ubuntu)

## 1. Create project root
```bash
sudo mkdir -p /srv/gosha
sudo chown -R "$USER":"$USER" /srv/gosha
cd /srv/gosha
```

## 2. Put this repository in `/srv/gosha`

## 3. Install packages and build llama.cpp
```bash
chmod +x scripts/*.sh
./scripts/01_bootstrap_ubuntu.sh /srv/gosha
```

## 4. Create `.env`
```bash
./scripts/03_create_env.sh /srv/gosha
nano /srv/gosha/.env
```

Fill in:
- `TELEGRAM_BOT_TOKEN`
- `ALLOWED_TELEGRAM_USER_IDS`
- `ADMIN_TELEGRAM_USER_ID`

## 5. Smoke check
```bash
./scripts/07_smoke_check.sh /srv/gosha
```

## 6. Start manually
```bash
./scripts/04_start_llama_server.sh /srv/gosha
# open second shell
./scripts/05_run_bot.sh /srv/gosha
```

## 7. Or install systemd
```bash
./scripts/06_install_systemd.sh /srv/gosha "$USER"
```

## 8. Check logs
```bash
journalctl -u gosha-llama -f
journalctl -u gosha-bot -f
```
