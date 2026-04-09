# Testing and CI Strategy

## Test tiers

- **Unit**: deterministic logic (`tests/unit`)
- **Contract**: OpenAPI contract assertions (`tests/contract`)
- **Integration / E2E smoke**: API + DB + game loop (`tests/loop_test.py`)

## CI gates

### Pull requests
- Lint (`ruff`)
- Unit + contract tests (`pytest tests/unit tests/contract`)
- Integration smoke (`python tests/loop_test.py`) against ephemeral Postgres

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

Run fast tests:

```bash
pytest tests/unit tests/contract
```

Run loop smoke against local API:

```bash
python tests/loop_test.py
```
