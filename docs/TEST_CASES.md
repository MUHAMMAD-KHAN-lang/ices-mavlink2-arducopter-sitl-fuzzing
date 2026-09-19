# Test cases 1–7

## Case 1 — Completely random data

Completely random raw bytes are sent to the SITL TCP endpoint. The MAVLink packet structure is ignored so this case tests how the input path behaves when it receives data that is not necessarily a MAVLink frame.

Observed run: 100 tests, random length 1–1000 bytes, no crash detected.

## Case 2 — Message IDs + random payload lengths

For each message ID from 0 to 255, payload lengths from 1 to 255 are exercised with deterministic random payload bytes. This is the main semi-valid MAVLink 2 fuzzing matrix and is intended to exercise deeper parser/message-handling paths.

Total: 65,280 test cases. The first implementation developed TCP backpressure; a corrected run was started, but the complete clean 65,280-case result remains pending.

## Case 3 — Zero-byte payload

A MAVLink 2 frame is constructed for each message ID from 0 to 255 with payload length exactly zero. This isolates handling of empty payloads and checks behaviour that should not depend on payload contents.

Observed run: 256/256 completed, no crash detected.

## Case 4 — All-zero payload

Message ID 0 is kept fixed and the payload is filled entirely with `00` bytes. Payload length increases from 1 to 255 bytes, stressing minimum-value data patterns and length boundaries.

Observed run: 255/255 completed, no crash detected.

## Case 5 — All-FF payload

Message ID 0 is kept fixed and the payload is filled entirely with `FF` bytes. Payload length increases from 1 to 255 bytes, exercising maximum byte values across increasing frame sizes.

Observed run: 255/255 completed, no crash detected.

## Case 6 — Random payload with increasing length

Message ID 0 is kept fixed while the payload contains deterministic random bytes and grows from 1 to 255 bytes. This combines complete MAVLink 2 framing and random payload content while keeping the message ID constant.

Observed run: 255/255 completed, no crash detected.

## Case 7 — Declared length mismatch (-1 / +1)

The payload-length field is deliberately made different from the number of payload bytes placed on the wire. Subcase 7A declares one byte less; subcase 7B declares one byte more.

The MAVLink 2 adaptation uses 255 `-1` tests and 254 `+1` tests because the length field is one byte and `255+1` cannot be represented without wrapping. Total: 509 tests. Observed result: 509/509 completed, no crash detected.
