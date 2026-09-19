# MAVLink 2 Fuzzing of ArduCopter SITL for ICES

A reproducible, lab-only MAVLink 2 fuzzing setup for ArduPilot/ArduCopter Software-in-the-Loop (SITL), developed as a security/robustness work package relevant to the ICES (Intranet Communications in Emergency Situations) program.

The project is a **modern MAVLink 2 adaptation** of the 2016 paper:

> Karel Domin, Iraklis Symeonidis, Eduard Marin, **“Security Analysis of the Drone Communication Protocol: Fuzzing the MAVLink protocol”**, 2016.

The original paper constructs MAVLink 1 frames (`FE`). This repository does **not** reproduce that wire format. The implementation here targets the current ArduCopter SITL environment and constructs MAVLink 2 frames (`FD`) where a structured MAVLink frame is required.

Paper record: https://hdl.handle.net/10993/37613
Official repository record: https://orbilu.uni.lu/handle/10993/37613

## Purpose

The goal is to test how a modern ArduCopter SITL instance behaves when its MAVLink/TCP input receives random, boundary, malformed, or length-inconsistent data. The experiments are intended for a controlled simulation environment only; no real aircraft is required or targeted.

For ICES, this work is relevant because UAV communication nodes are part of an emergency/disaster communications architecture. The fuzzing stage provides a pre-integration robustness/security check for the UAV autopilot communication endpoint. It is not, by itself, a complete security assessment of the ICES network.

## Architecture

```text
Windows fuzzing host
    |
    | TCP 192.168.18.6:5760
    v
Ubuntu 26.04 ArduCopter SITL
    |
    +--> MAVLink 2 parser / flight stack

Ubuntu SITL monitor
    |
    | TCP 192.168.18.6:9001
    v
Windows fuzzing scripts
```

Two independent TCP services are used:

* **5760** — ArduCopter SITL MAVLink/TCP endpoint.
* **9001** — small Ubuntu monitor that reports whether the `arducopter` process is running and whether port 5760 is listening.

## Environment used

### Ubuntu

* Ubuntu 26.04.1 LTS
* Python 3.14.4
* ArduPilot source tree: `~/ardupilot`
* Python virtual environment: `~/ardupilot/.venv`
* Waf 2.0.27
* GCC/G++ 15.2.0 in the observed build
* ArduCopter SITL executable: `build/sitl/bin/arducopter`

### Windows

* Python virtual environment
* `pymavlink`
* Fuzzer scripts in Python

## Repository layout

```text
.
├── README.md
├── LICENSE
├── CITATION.cff
├── requirements.txt
├── .gitignore
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SETUP_UBUNTU.md
│   ├── SETUP_WINDOWS.md
│   ├── TEST_CASES.md
│   ├── CASE_MAPPING_TO_PAPER.md
│   ├── MAVLINK2_PACKET_FORMAT.md
│   ├── RESULTS.md
│   ├── ROBUST_TESTING_REMAINING.md
│   ├── PAPER_REFERENCE.md
│   └── CLOUD_AI_GITHUB_INSTRUCTIONS.md
├── scripts/
│   ├── ubuntu/
│   │   └── sitl_monitor.py
│   ├── windows/            # cleaned release copies — run these
│   │   ├── baseline_connection.py
│   │   ├── case1.py ... case7.py
│   └── as-run/             # exact code that produced the published logs
│       ├── case1.py ... case7.py
│       ├── exploratory_first.py
│       └── exploratory_mav.py
├── results/
│   └── RESULTS_SUMMARY.md
└── logs/                   # raw evidence
    ├── README.md
    ├── case1/              # 100 per-test files
    └── case2_results.txt ... case7_results.txt
```

### Two copies of the case scripts

`scripts/windows/` holds the cleaned release versions and is what the setup
docs refer to. `scripts/as-run/` holds the working scripts exactly as they were
when the logs in `logs/` were generated. They implement the same experiment but
are not byte-identical — see `logs/README.md` for the differences. Both are
published so that the evidence and the code that produced it can be checked
against each other.

## Setup and execution order

1. Build ArduCopter SITL on Ubuntu.
2. Start ArduCopter on TCP port 5760.
3. Start `sitl_monitor.py` on Ubuntu port 9001.
4. Create the Windows Python virtual environment and install `pymavlink`.
5. Run `baseline_connection.py` to verify the network/MAVLink path.
6. Run Case 1 through Case 7 individually.
7. Keep the generated `Fuzz_logs/*.txt` files with the repository when publishing experiment evidence.

Detailed commands and explanations are in `docs/SETUP_UBUNTU.md` and `docs/SETUP_WINDOWS.md`.

## Test cases implemented

| Case | Condition | Tests | Observed result |
|---|---|---:|---|
| 1 | Completely random raw bytes, 1–1000 bytes | 100 | No crash detected |
| 2 | Message IDs 0–255 with random payload lengths 1–255 | 65,280 | Corrected rerun started; full clean rerun remains pending |
| 3 | Zero-payload MAVLink 2 frame for each message ID 0–255 | 256 | 256/256, no crash detected |
| 4 | Message ID 0, all-`00` payload, lengths 1–255 | 255 | 255/255, no crash detected |
| 5 | Message ID 0, all-`FF` payload, lengths 1–255 | 255 | 255/255, no crash detected |
| 6 | Message ID 0, random payload, lengths 1–255 | 255 | 255/255, no crash detected |
| 7 | Declared payload length differs from actual by -1 and +1 | 509 | 509/509, no crash detected |

**Important:** “No crash detected” means the monitor did not observe an `arducopter` process termination or loss of the 5760 listening socket at the time of the check. It does not prove absence of parser errors, memory corruption, logic bugs, or security vulnerabilities.

## Important modernization notes

The paper’s original implementation was written for MAVLink 1 and used a fixed magic byte `FE`. In this project:

* MAVLink 2 is used for structured frames (`FD`).
* MAVLink 2 has a 3-byte message ID field.
* The MAVLink 2 CRC-extra value is taken from the installed `pymavlink` message map.
* Case 7 is adapted to the one-byte MAVLink 2 payload-length field, so the `+1` side stops at actual length 254 rather than wrapping 255+1 to zero.
* Cases 4–6 keep message ID 0 fixed in this implementation so the payload mutation is isolated and reproducible. That is an implementation choice, not a claim that the original paper used the same fixed ID.

See `docs/CASE_MAPPING_TO_PAPER.md` for the detailed mapping.

## Scope and safety

This repository is designed for a local ArduPilot SITL lab. Do not point these scripts at a real aircraft, an external drone, or a third-party network. See `docs/ROBUST_TESTING_REMAINING.md` for the next research steps needed to turn these baseline tests into a stronger security test campaign.
