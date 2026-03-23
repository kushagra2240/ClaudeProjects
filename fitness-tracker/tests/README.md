# Parser Tests

These scripts test the Mi Fitness and Runkeeper parsers using synthetic data
that mirrors the real export format. No credentials or phone access needed.

## Run all tests

```bash
# From the fitness-tracker/ directory with venv active
python -m pytest tests/ -v
```

## Run a single test file

```bash
python -m pytest tests/test_mi_fitness_parser.py -v
python -m pytest tests/test_runkeeper_parser.py -v
```

## What is being tested

| Test | What it checks |
|------|---------------|
| `test_mi_fitness_parser.py` | Steps, heart rate, sleep, activities all parse correctly from a synthetic ZIP |
| `test_runkeeper_parser.py` | cardioActivities.csv parses correctly; GPX enrichment works |
| `test_upload_endpoints.py` | The FastAPI upload endpoints accept ZIPs and return correct counts |

## Why there's no "login to Mi Fitness / Runkeeper" test

Neither service supports programmatic access without a manual step:

- **Mi Fitness** — Xiaomi has no public API. Data is only accessible via the
  in-app "Export Personal Data" ZIP download.
- **Runkeeper** — Has a HealthGraph OAuth API, but it requires registering a
  developer application and completing an OAuth flow in a browser. It cannot
  be automated in a test script without user interaction.

The parsers are the only thing that can be unit-tested in isolation.
To test a real export, drop your actual ZIP into `tests/fixtures/` and run
`python tests/test_real_export.py path/to/your/export.zip`.
