# Experimental results

## Recorded results from the current work

| Case | Condition | Tests | Status |
|---|---|---:|---|
| 1 | Completely random raw data, 1–1000 bytes | 100 | No crash detected |
| 2 | Message IDs 0–255 × payload lengths 1–255, random payload | 65,280 planned | Corrected rerun started; complete clean run still pending |
| 3 | Zero-byte payload, message IDs 0–255 | 256 | 256/256, no crash detected |
| 4 | All `00` payload, lengths 1–255 | 255 | 255/255, no crash detected |
| 5 | All `FF` payload, lengths 1–255 | 255 | 255/255, no crash detected |
| 6 | Random payload, lengths 1–255 | 255 | 255/255, no crash detected |
| 7 | Declared length -1 and +1 from actual | 509 | 509/509, no crash detected |

## Case 2 history

The first Case 2 implementation used a persistent connection and sent too quickly. Ubuntu showed an established connection with approximately 2.25 MB in `Recv-Q`, while ArduCopter remained alive. This was interpreted as TCP backpressure rather than a SITL crash.

A second harness was developed with a controlled per-test connection and a 0.1 s processing delay. A clean run was restarted from test 1 after restarting SITL and was observed successfully through at least test 356. The complete 65,280-test run was not captured as a finished result in the recorded work and should therefore remain marked pending.

## Interpretation

“No crash detected” is intentionally conservative. The monitor only establishes that the `arducopter` process was running and port 5760 was listening when checked. It does not establish code coverage, absence of assertions, absence of memory errors, absence of silent state corruption, or full functional correctness.
