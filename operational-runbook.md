# Mystic Weave — Operational Runbook (Local + Railway)

Lightweight troubleshooting checklist for common runtime and deployment issues.

---

## 1) Local startup sanity checks

### Symptoms
- API fails on startup
- `/health` not reachable
- DB errors during startup

### Checklist
1. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
2. Ensure env is set:
   ```bash
   cp .env.example .env
   ```
3. Confirm `DATABASE_URL` in `.env` points to a reachable Postgres.
4. Apply migrations:
   ```bash
   alembic upgrade head
   ```
5. Start server:
   ```bash
   uvicorn api.main:app --host 127.0.0.1 --port 8000
   ```
6. Verify:
   ```bash
   curl -sf http://127.0.0.1:8000/health
   curl -sf http://127.0.0.1:8000/version
   ```

---

## 2) Port/process conflicts

### Symptoms
- Uvicorn reports address already in use
- `loop_test.py` hits stale behavior

### Checklist
```bash
lsof -i :8000
```
Kill stale process if needed, then restart uvicorn.

---

## 3) Migration/schema issues

### Symptoms
- Missing table/column errors (`game_states`, `locations`, `world_graph`)

### Checklist
1. Ensure migration files exist in `alembic/versions/`.
2. Run:
   ```bash
   alembic upgrade head
   ```
3. Retry startup.

---

## 4) Contract drift / CI failures

### Symptoms
- CI fails on contract or guard checks

### Local repro commands
```bash
python3 scripts/check_openapi_drift.py
python3 scripts/validate_data_files.py
python3 scripts/validate_prompts.py
pytest -q tests/unit tests/contract tests/regression/test_endpoint_validation.py tests/regression/test_multi_turn_persistence.py
```

---

## 5) Pre-deploy bundle verification

### Local preflight
Start API locally, then run:
```bash
python3 scripts/predeploy_smoke_bundle.py http://127.0.0.1:8000
```

### CI equivalent
- `.github/workflows/predeploy.yml` runs the same guard + regression + smoke sequence.

---

## 6) Railway troubleshooting

### Symptoms
- Deployment unhealthy
- Runtime DB connection failures

### Checklist
1. Confirm Railway service has Postgres plugin attached.
2. Confirm app service has `DATABASE_URL` injected.
3. Verify start command:
   ```toml
   uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```
4. Check live endpoints:
   - `/health`
   - `/version`
5. Run production contract verification:
   ```bash
   python3 scripts/verify_production_contract.py https://mysticweave-production.up.railway.app
   ```

---

## 7) Quick rollback posture

If a deployment regresses:
1. Re-run predeploy checks locally on the target commit.
2. Revert the offending commit on `main`.
3. Re-run production verify workflow after redeploy.

---

## 8) Escalation bundle to capture

When opening an issue, include:
- failing command + output
- `git rev-parse HEAD`
- `curl /version` response
- relevant CI job URL/log artifact
