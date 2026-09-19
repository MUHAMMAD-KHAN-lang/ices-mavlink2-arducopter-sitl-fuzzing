# Windows / fuzzer setup

The fuzzing scripts were run from Windows using a Python virtual environment. Ubuntu hosted the ArduCopter SITL instance.

## 1. Create and activate the virtual environment

In PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

* `python -m venv .venv` creates the Windows virtual environment.
* `.venv\Scripts\Activate.ps1` activates it in PowerShell.

## 2. Install pymavlink

```powershell
python -m pip install pymavlink
```

This installs the Python MAVLink tooling used by the baseline connection check and the MAVLink 2 packet construction used in Cases 2–7.

## 3. Baseline connection

Run:

```powershell
python scripts\windows\baseline_connection.py
```

The baseline connects to:

```text
TCP 192.168.18.6:5760
```

and waits for an ArduCopter heartbeat. The observed raw heartbeat started with `FD`, confirming MAVLink 2 traffic in the current SITL environment.

## 4. Test sequence

Run each case separately:

```powershell
python scripts\windows\case1.py
python scripts\windows\case2.py
python scripts\windows\case3.py
python scripts\windows\case4.py
python scripts\windows\case5.py
python scripts\windows\case6.py
python scripts\windows\case7.py
```

Do not run multiple fuzzers simultaneously against the same SITL TCP port.

## 5. Text logging

The scripts write human-readable `.txt` results under `Fuzz_logs/`. The logs record identifiers, lengths, payload bytes, full frame hex where applicable, TCP status, SITL process status, port status, and the monitor result.
