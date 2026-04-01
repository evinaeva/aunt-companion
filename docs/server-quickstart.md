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

## 4. Create runtime config (`.env` + Gemini TOML)
```bash
./scripts/03_create_env.sh /srv/gosha
nano /srv/gosha/.env
cp /srv/gosha/config/llm.example.toml /srv/gosha/config/llm.local.toml
nano /srv/gosha/config/llm.local.toml
```

Fill in:
- `.env`: `TELEGRAM_BOT_TOKEN`, `ALLOWED_TELEGRAM_USER_IDS`, `ADMIN_TELEGRAM_USER_ID`
- `config/llm.local.toml` `[primary].api_key` for Gemini model `gemini-2.5-flash-lite`

## 5. Smoke check
```bash
./scripts/07_smoke_check.sh /srv/gosha
```

## 6. Start manually
```bash
# optional: start local llama secondary backend
./scripts/04_start_llama_server.sh /srv/gosha
# bot (Telegram chat uses primary provider from config/llm.local.toml)
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
