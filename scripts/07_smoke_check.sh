#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-$(pwd)}"
cd "$PROJECT_ROOT"

if [ ! -f ".env" ]; then
  echo "Missing .env at $PROJECT_ROOT/.env" >&2
  exit 1
fi

source .venv/bin/activate
set -a
source .env
set +a

echo "[smoke] checking python imports"
python -c "import app.main; import app.telegram; import app.db; print('ok: imports')"

echo "[smoke] checking environment + settings"
python -c "from app.config import get_settings; s=get_settings(); print(f'ok: env={s.environment} db={s.paths.sqlite_path}')"

echo "[smoke] checking sqlite initialization"
python - <<'PY'
import asyncio
from app.config import get_settings
from app.db import initialize_database

async def main() -> None:
    s = get_settings()
    await initialize_database(
        db_path=s.paths.sqlite_path,
        data_dir=s.paths.data_dir,
        tmp_dir=s.paths.tmp_dir,
        log_dir=s.paths.log_dir,
    )
    print("ok: sqlite initialized")

asyncio.run(main())
PY

echo "[smoke] checking llama endpoint (optional)"
if curl -fsS "${LLM_BASE_URL%/}/health" >/dev/null 2>&1; then
  echo "ok: llama health endpoint reachable"
else
  echo "warn: llama endpoint not reachable at ${LLM_BASE_URL%/}/health"
fi

echo "[smoke] complete"
