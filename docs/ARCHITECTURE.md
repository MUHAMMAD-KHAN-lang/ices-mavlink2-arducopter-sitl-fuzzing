# Experiment architecture

```text
                   Local lab / LAN

+---------------------------+             +-----------------------------+
| Windows Python fuzzer     |             | Ubuntu 26.04.1              |
|                           |             |                             |
| baseline_connection.py    | TCP :5760  | ArduCopter SITL              |
| case1.py ... case7.py ----+------------>| build/sitl/bin/arducopter    |
|                           |             |                             |
|                           |             | TCP :9001                    |
|                           |<------------+ sitl_monitor.py              |
+---------------------------+  JSON status +-----------------------------+
```

## Data flow

1. ArduCopter SITL listens on TCP 5760.
2. The Windows fuzzer connects to 5760 and sends either raw bytes or constructed MAVLink 2 frames.
3. The Ubuntu monitor is a separate TCP service on 9001.
4. After each test or monitoring checkpoint, the fuzzer asks the monitor for:
   * `SITL_PROCESS`
   * `PORT_5760`
   * `RESULT`
5. Each test is logged as plain text for reproduction.

## Why the monitor is separate

The Windows process cannot directly call Linux `pgrep`/`ss` for the Ubuntu process. The small Ubuntu monitor provides a minimal status interface without requiring SSH or a full remote-execution framework.
