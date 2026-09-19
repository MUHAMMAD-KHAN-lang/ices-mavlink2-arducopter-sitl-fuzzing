# Mapping from the 2016 paper to this MAVLink 2 implementation

The original paper describes seven conceptual test cases around MAVLink 1. This repository keeps the seven-case structure while adapting the frame construction and execution method to a modern MAVLink 2 ArduCopter SITL.

| Paper concept | This repository | Main adaptation |
|---|---|---|
| Case 1: completely random data | Raw random bytes, 1–1000 bytes | Raw TCP bytes are sent to a MAVLink 2 SITL endpoint; packet structure is ignored |
| Case 2: every message ID, payload 1–255 with random hex payload | Message IDs 0–255 × payload lengths 1–255 | MAVLink 2 frame (`FD`), three-byte message ID, MAVLink 2 CRC-extra handling |
| Case 3: no payload | Message IDs 0–255 with zero payload | MAVLink 2 frame construction |
| Case 4: minimum byte values | Fixed MsgID 0, lengths 1–255, all `00` | Fixed MsgID chosen here to isolate payload pattern |
| Case 5: maximum byte values | Fixed MsgID 0, lengths 1–255, all `FF` | Fixed MsgID chosen here to isolate payload pattern |
| Case 6: random payload with increasing length | Fixed MsgID 0, lengths 1–255, deterministic random payload | Structured MAVLink 2 frames with reproducible random payloads |
| Case 7: declared length mismatch | 7A declared=actual-1, 7B declared=actual+1 | MAVLink 2 one-byte length field; +1 stops at actual 254 |

## Why not reproduce the paper literally?

The paper's setup and packet format are historical. It describes MAVLink 1 framing with `FE`, whereas the current ArduCopter SITL environment observed in this project emits MAVLink 2 traffic beginning with `FD`.

The goal of this repository is therefore methodological continuity: reproduce the **fuzzing ideas** under a current MAVLink 2 implementation, document every adaptation, and avoid falsely presenting an old MAVLink 1 packet generator as a MAVLink 2 experiment.
