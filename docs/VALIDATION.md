# Script validation

Before committing changes, run a Python syntax check from the repository root:

```bash
python -m py_compile scripts/ubuntu/sitl_monitor.py scripts/windows/*.py
```

This checks syntax only; it does not run the fuzzer or connect to SITL.

For a live smoke test, start SITL and the monitor first, then run `baseline_connection.py` before any fuzzing case.
