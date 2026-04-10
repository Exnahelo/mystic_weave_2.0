# Testing and CI Strategy

## Test tiers

- **Unit**: deterministic logic (`tests/unit`)
- **Contract**: OpenAPI contract assertions (`tests/contract`)
- **Integration / E2E smoke**: API + DB + game loop (`tests/loop_test.py`)

## CI gates

### Pull requests
- Lint (`ruff`)
- OpenAPI drift check (`python scripts/check_openapi_drift.py`)
- Data validation (`python scripts/validate_data_files.py`)
- Prompt validation (`python scripts/validate_prompts.py`)
- Unit + contract tests (`pytest tests/unit tests/contract`)
- Regression persistence tests (`tests/regression/test_endpoint_validation.py`, `tests/regression/test_multi_turn_persistence.py`)
- Integration smoke (`python tests/loop_test.py`) against ephemeral Postgres
- Pre-deploy bundle workflow (`.github/workflows/predeploy.yml`) for contract + smoke gating

### Push to `main`
- Same as pull request

### Nightly
- Unit + contract regression set
- Full loop smoke against fresh Postgres service
- Production contract/options/version verification (`scripts/verify_production_contract.py`)

## Local commands

Install development tooling:

```bash
pip install -r requirements-dev.txt
```

Run lint:

```bash
ruff check api core tests
```

Run OpenAPI drift check:

```bash
python scripts/check_openapi_drift.py
```

Run data + prompt validators:

```bash
python scripts/validate_data_files.py
python scripts/validate_prompts.py
```

Run pre-deploy smoke bundle (against running API):

```bash
python scripts/predeploy_smoke_bundle.py http://127.0.0.1:8000
```

Run fast tests:

```bash
pytest tests/unit tests/contract
```

Run regression persistence tests:

```bash
pytest tests/regression/test_endpoint_validation.py tests/regression/test_multi_turn_persistence.py
```

Run loop smoke against local API:

```bash
python tests/loop_test.py
```

Ensure DB schema is current before starting the app:

```bash
alembic upgrade head
```

Operational troubleshooting reference:
- `OPERATIONAL_RUNBOOK.md`
