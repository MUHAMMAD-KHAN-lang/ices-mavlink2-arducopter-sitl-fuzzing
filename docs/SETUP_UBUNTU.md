# Ubuntu / ArduPilot SITL setup

This document records the setup used for the lab environment.

## 1. Get ArduPilot

```bash
git clone https://github.com/ArduPilot/ardupilot.git
cd ardupilot
git submodule update --init --recursive
```

* `git clone` downloads the ArduPilot source tree.
* `cd ardupilot` enters the source directory.
* `git submodule update --init --recursive` initializes ArduPilot's nested dependencies, including MAVLink-related sources and other modules.

If you already have the repository, only the last two commands are normally needed.

## 2. Create the Python virtual environment

The environment used in the experiment was Python 3.14.4.

```bash
sudo apt install python3-venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install empy==3.3.4 pexpect future
```

Command meaning:

* `python3 -m venv .venv` creates an isolated Python environment inside `.venv`.
* `source .venv/bin/activate` activates that environment for the current shell.
* `python -m pip ...` uses the active environment's Python/pip.
* `empy==3.3.4`, `pexpect`, and `future` were installed to satisfy the build path used during this setup.

### Note about the full ArduPilot prerequisite script

On Ubuntu 26.04 in this specific setup, the full prerequisite script encountered a long wxPython build and an `Errno 122: Disk quota exceeded` failure. The experiment therefore proceeded by installing the build dependencies that Waf actually required instead of repeatedly retrying the same wxPython path.

## 3. Configure SITL

```bash
./waf configure --board sitl
```

This configures the ArduPilot build system for Software-in-the-Loop. After the virtual environment was activated and Waf was reconfigured, it used the virtual-environment Python executable.

## 4. Build ArduCopter

```bash
./waf copter
```

This builds the ArduCopter SITL binary. The successful build produced:

```text
build/sitl/bin/arducopter
```

The build generated MAVLink 2 C implementations and reported the current ArduPilot tree's MAVLink message definitions.

## 5. Start ArduCopter SITL

The experiment used a standalone SITL invocation similar to:

```bash
./build/sitl/bin/arducopter --home -35.36321,149.165320,500,270 --model quad --speedup 10 --wipe
```

Meaning:

* `./build/sitl/bin/arducopter` — launches the built simulator.
* `--home` — sets the simulated vehicle's initial latitude, longitude, altitude, and heading.
* `--model quad` — uses a quadcopter model.
* `--speedup 10` — runs the simulation faster than real time.
* `--wipe` — starts with wiped SITL state/storage.

Expected network line:

```text
SERIAL0 on TCP port 5760
```

## 6. Verify port 5760

```bash
ss -lntp | grep ':5760'
```

Meaning:

* `ss` — displays sockets.
* `-l` — listening sockets.
* `-n` — numeric addresses/ports.
* `-t` — TCP sockets.
* `-p` — owning process.
* `grep ':5760'` — filters for SITL's port.

Expected result resembles:

```text
LISTEN ... 0.0.0.0:5760 ... users:(("arducopter",pid=...,fd=10))
```

## 7. Verify established fuzzing connections when needed

```bash
ss -tnp | grep ':5760'
```

This is useful when diagnosing TCP backpressure, connection state, or a stuck test harness.

## 8. SITL monitor

Run this in a second Ubuntu terminal:

```bash
python3 scripts/ubuntu/sitl_monitor.py
```

The monitor listens on TCP port `9001`. It checks:

* whether the `arducopter` process exists;
* whether TCP port 5760 is listening.

It returns a JSON status to the Windows fuzzing scripts.
