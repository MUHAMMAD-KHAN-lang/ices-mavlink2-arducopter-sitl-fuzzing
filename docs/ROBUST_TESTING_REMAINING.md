# Robust testing still remaining

The seven baseline cases are a useful first layer, but they are not a complete security assessment. The following work remains important before describing the implementation as a robust fuzzing campaign.

## 1. Complete Case 2

Run the corrected Case 2 harness from test 1 through all 65,280 combinations and preserve the resulting text log.

## 2. Capture stdout/stderr and crash evidence

The current monitor checks process and port state. A stronger harness should capture the SITL terminal output and retain:

* assertion failures;
* parser warnings/errors;
* signals and exit codes;
* core dumps;
* GDB backtraces when a crash occurs.

The original paper explicitly used GDB/core dumps to investigate failures.

## 3. Use sanitizers and debug builds

Repeat interesting inputs with appropriate ASan/UBSan/debug instrumentation where supported by the build environment.

## 4. Coverage and path depth

The current cases are input-pattern tests. Add code coverage or parser-path feedback so that tests can be prioritized by unexplored execution paths rather than only by length and byte pattern.

## 5. Expand semantic message coverage

Cases 4–6 intentionally keep MsgID 0 fixed in this repository. A future campaign should systematically apply the same boundary payload patterns to each known MAVLink message definition and respect each message's semantic field layout when desired.

## 6. Regression corpus

Any input that produces anomalous behaviour should be minimized, stored as text, assigned a stable test ID, and added to a regression suite.

## 7. Version matrix

Repeat the campaign against explicitly versioned ArduPilot builds so findings can be associated with a reproducible software revision.

## 8. ICES-specific integration testing

After SITL robustness testing, the ICES program should test the actual network architecture: multiple UAV/ground communication nodes, realistic link loss, latency, packet loss, reordering, bandwidth constraints, and recovery behaviour. MAVLink fuzzing should be treated as one security/robustness layer inside the larger ICES validation plan.
